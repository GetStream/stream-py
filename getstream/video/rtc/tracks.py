"""
Consolidated track management module for video streaming.
Handles track publishing, subscription configuration, and subscription management.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pyee.asyncio import AsyncIOEventEmitter

from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2
from getstream.video.rtc.pb.stream.video.sfu.models.models_pb2 import (
    TrackType,
    VideoDimension,
)
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc import signal_pb2
from getstream.video.rtc.twirp_client_wrapper import SfuRpcError

logger = logging.getLogger(__name__)


@dataclass
class TrackSubscriptionConfig:
    """Subscription rules for a participant role."""

    # Track types to subscribe to (audio by default)
    track_types: List[int] = field(default_factory=lambda: [])

    # Preferred dimensions
    video_dimension: VideoDimension = field(
        default_factory=lambda: VideoDimension(width=1920, height=1080)
    )
    screenshare_dimension: VideoDimension = field(
        default_factory=lambda: VideoDimension(width=1920, height=1080)
    )


@dataclass
class SubscriptionConfig:
    """Top-level subscription configuration.

    Attributes
    ----------
    default : TrackSubscriptionConfig
        Fallback rule when no role-specific rule matches.
    role_filters : Dict[str, TrackSubscriptionConfig]
        Mapping of role → rule.
    max_subscriptions : Optional[int]
        Global cap on active subscriptions.
    """

    default: TrackSubscriptionConfig = field(
        default_factory=lambda: TrackSubscriptionConfig()
    )
    role_filters: Dict[str, TrackSubscriptionConfig] = field(default_factory=dict)
    max_subscriptions: Optional[int] = None


class SubscriptionManager(AsyncIOEventEmitter):
    """Encapsulates remote track subscription policy & SFU UpdateSubscriptions plumbing."""

    def __init__(
        self,
        connection_manager: "Any",
        subscription_config: Optional[SubscriptionConfig] = None,
    ) -> None:
        super().__init__()
        self.connection_manager = connection_manager
        self._subscription_config = subscription_config or SubscriptionConfig()
        self._subscribed_track_details: List[signal_pb2.TrackSubscriptionDetails] = []
        self._expected_tracks: Dict[
            str, models_pb2.Participant
        ] = {}  # track_type:user_id:session_id -> participant
        self._received_track_order: List[
            str
        ] = []  # Track the order of received WebRTC tracks
        self._lock = asyncio.Lock()

    def _get_role_config(
        self, participant: Optional[models_pb2.Participant]
    ) -> Optional[TrackSubscriptionConfig]:
        """Determine which TrackSubscriptionConfig applies to the participant."""
        if not self._subscription_config:
            return None

        roles = set(getattr(participant, "roles", [])) if participant else set()

        for role in roles:
            if role in self._subscription_config.role_filters:
                return self._subscription_config.role_filters[role]

        return self._subscription_config.default

    def _should_subscribe(
        self, participant: Optional[models_pb2.Participant], track_type: int
    ) -> bool:
        """Check if a given track should be subscribed according to role config."""
        cfg = self._get_role_config(participant)
        return bool(cfg and track_type in cfg.track_types)

    def _create_track_subscription_detail(
        self,
        participant: Optional[models_pb2.Participant],
        track_type: int,
        user_id: str,
        session_id: str,
    ) -> Optional[signal_pb2.TrackSubscriptionDetails]:
        """Generate TrackSubscriptionDetails using role-based dimension preferences."""
        cfg = self._get_role_config(participant)
        if not cfg:
            return None

        try:
            detail = signal_pb2.TrackSubscriptionDetails(
                user_id=user_id,
                session_id=session_id,
                track_type=track_type,
            )

            if track_type == TrackType.TRACK_TYPE_VIDEO and cfg.video_dimension:
                detail.dimension.CopyFrom(cfg.video_dimension)
            elif (
                track_type == TrackType.TRACK_TYPE_SCREEN_SHARE
                and cfg.screenshare_dimension
            ):
                detail.dimension.CopyFrom(cfg.screenshare_dimension)

            return detail
        except Exception as e:
            logger.error(f"Error creating TrackSubscriptionDetails: {e}")
            return None

    def _generate_subscription_details_for_participants(
        self,
    ) -> List[signal_pb2.TrackSubscriptionDetails]:
        """Generate subscription details for all current participants based on policy."""
        subscription_infos: List[signal_pb2.TrackSubscriptionDetails] = []

        for (
            participant
        ) in self.connection_manager.participants_state._participant_by_prefix.values():
            if participant.session_id == self.connection_manager.session_id:
                continue  # Skip our own tracks

            if not participant.published_tracks:
                continue

            for track_type in participant.published_tracks:
                if not self._should_subscribe(participant, track_type):
                    continue

                detail = self._create_track_subscription_detail(
                    participant,
                    track_type,
                    participant.user_id,
                    participant.session_id,
                )

                if detail is None:
                    continue

                subscription_infos.append(detail)

                # Respect max-subscription limit if set
                if (
                    self._subscription_config.max_subscriptions is not None
                    and len(subscription_infos)
                    >= self._subscription_config.max_subscriptions
                ):
                    return subscription_infos

        return subscription_infos

    async def _update_subscriptions(self):
        """Push the current subscription list to the SFU."""
        async with self._lock:
            track_details = list(self._subscribed_track_details)

        if not track_details or not self.connection_manager.twirp_signaling_client:
            return

        try:
            response = await self.connection_manager.twirp_signaling_client.UpdateSubscriptions(
                ctx=self.connection_manager.twirp_context,
                request=signal_pb2.UpdateSubscriptionsRequest(
                    session_id=self.connection_manager.session_id,
                    tracks=track_details,
                ),
                server_path_prefix="",
            )
            logger.debug(f"Updated subscriptions for req: {track_details} - {response}")
        except SfuRpcError as e:
            logger.error(f"Failed to update subscriptions SfuRpcError: {e}")
        except Exception as e:
            logger.error(f"Failed to update subscriptions: {e}")

    async def handle_track_published(self, event):
        """Handle new remote track publications from the SFU."""
        logger.error(
            f"Handling track published: {event.user_id} - {event.session_id} - {event.type}"
        )
        try:
            # Keep participants state up-to-date
            if hasattr(event, "participant"):
                self.connection_manager.participants_state.add_participant(
                    event.participant
                )

                # Register expected track for this user
                track_type = getattr(event, "type", None)
                if track_type == TrackType.TRACK_TYPE_AUDIO:
                    track_key = f"{track_type}:{event.user_id}:{event.session_id}"
                    self._expected_tracks[track_key] = event.participant

            track_type = getattr(event, "type", None)
            if track_type is None:
                logger.error(f"Track type is None: {event}")
                return

            if not self._should_subscribe(
                getattr(event, "participant", None), track_type
            ):
                logger.error(f"Not subscribing to track: {event}")
                return

            # Check for duplicates & subscription limits
            async with self._lock:
                already_subscribed = any(
                    d.user_id == event.user_id
                    and d.session_id == event.session_id
                    and d.track_type == track_type
                    for d in self._subscribed_track_details
                )
                if already_subscribed:
                    logger.error(f"Already subscribed to track: {event}")
                    return

                if (
                    self._subscription_config.max_subscriptions is not None
                    and len(self._subscribed_track_details)
                    >= self._subscription_config.max_subscriptions
                ):
                    logger.error(
                        "Max subscription limit reached, skipping new track subscription"
                    )
                    return

                detail = self._create_track_subscription_detail(
                    event.participant,
                    track_type,
                    event.user_id,
                    event.session_id,
                )
                if detail is None:
                    logger.error(f"Detail is None: {event}")
                    return

                self._subscribed_track_details.append(detail)

            # Push updated subscriptions to SFU outside the lock
            await self._update_subscriptions()

        except Exception as e:
            logger.error(f"Error handling track published: {e}")

    async def handle_track_unpublished(self, event):
        """Handle remote track unpublication events."""
        try:
            track_type = getattr(event, "type", None)
            user_id = getattr(event, "user_id", None)
            session_id = getattr(event, "session_id", None)

            if track_type is None:
                return

            async with self._lock:
                before = len(self._subscribed_track_details)
                self._subscribed_track_details = [
                    d
                    for d in self._subscribed_track_details
                    if not (
                        d.user_id == user_id
                        and d.session_id == session_id
                        and d.track_type == track_type
                    )
                ]
                after = len(self._subscribed_track_details)

                if before == after:
                    return  # nothing changed

            await self._update_subscriptions()

        except Exception as e:
            logger.error(f"Error handling track unpublished: {e}")

    def get_next_expected_audio_user(self) -> Optional[models_pb2.Participant]:
        """Get the next expected user for an incoming audio track."""
        # Find the first audio track expectation
        for track_key, participant in list(self._expected_tracks.items()):
            if track_key.startswith(f"{TrackType.TRACK_TYPE_AUDIO}:"):
                # Remove this expectation since we're using it
                del self._expected_tracks[track_key]
                return participant

        return None
