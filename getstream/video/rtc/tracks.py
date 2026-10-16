"""
Subscription configuration for remote tracks.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from getstream.video.rtc.pb.stream.video.sfu.models.models_pb2 import (
    VideoDimension,
)


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
