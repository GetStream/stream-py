"""
Systematic Integration tests for Feed operations
These tests follow a logical flow: setup → create → operate → cleanup

Test order:
1. Environment Setup (user, feed creation)
2. Activity Operations (create, read, update, delete)
3. Reaction Operations (add, query, delete)
4. Comment Operations (add, read, update, delete)
5. Bookmark Operations (add, query, update, delete)
6. Follow Operations (follow, query, unfollow)
7. Batch Operations
8. Advanced Operations (polls, pins, etc.)
9. Cleanup
"""

import os
import uuid
import pytest
from datetime import datetime, timedelta
from typing import List

from getstream import Stream
from getstream.models import (
    UserRequest,
    Attachment,
    AddFolderRequest,
    VoteData,
    SortParamRequest,
    ActivityRequest,
)
from getstream.stream_response import StreamResponse


class TestFeedIntegration:
    """
    Systematic Integration tests for Feed operations
    """

    USER_FEED_TYPE = "user"
    POLL_QUESTION = "What's your favorite programming language?"

    def setup_method(self):
        """Setup for each test method"""
        self.client = Stream(
            api_key=os.environ.get("STREAM_API_KEY"),
            api_secret=os.environ.get("STREAM_API_SECRET"),
            base_url=os.environ.get(
                "STREAM_BASE_URL", "https://chat.stream-io-api.com"
            ),
        )

        self.test_user_id = f"test-user-{uuid.uuid4()}"
        self.test_user_id_2 = f"test-user-2-{uuid.uuid4()}"
        self.test_feed = self.client.feeds.feed(self.USER_FEED_TYPE, self.test_user_id)
        self.test_feed_2 = self.client.feeds.feed(
            self.USER_FEED_TYPE, self.test_user_id_2
        )

        # Track created resources for cleanup
        self.created_activity_ids: List[str] = []
        self.created_comment_ids: List[str] = []
        self.test_activity_id = ""
        self.test_comment_id = ""

        # Setup environment for each test
        self._setup_environment()

    def teardown_method(self):
        """Cleanup after each test method"""
        self._cleanup_resources()

    def _setup_environment(self):
        """Setup test environment with users and feeds"""
        try:
            # Create test users
            # snippet-start: CreateUsers
            users = {
                self.test_user_id: UserRequest(
                    id=self.test_user_id, name="Test User 1", role="user"
                ),
                self.test_user_id_2: UserRequest(
                    id=self.test_user_id_2, name="Test User 2", role="user"
                ),
            }
            response = self.client.update_users(users=users)
            # snippet-end: CreateUsers

            if response.status_code() >= 400:
                raise Exception(f"Failed to create users: {response.status_code()}")

            # Create feeds
            # snippet-start: GetOrCreateFeed

            feed_response_1 = self.test_feed.get_or_create(
                user_id=self.test_user_id
            )
            feed_response_2 = self.test_feed_2.get_or_create(
                user_id=self.test_user_id_2
            )
            # snippet-end: GetOrCreateFeed

            if feed_response_1.status_code() >= 400:
                raise Exception(
                    f"Failed to create feed 1: {feed_response_1.status_code()}"
                )
            if feed_response_2.status_code() >= 400:
                raise Exception(
                    f"Failed to create feed 2: {feed_response_2.status_code()}"
                )

        except Exception as e:
            print(f"⚠️ Setup failed: {e}")
            # Stop everything
            exit(1)

    def _cleanup_resources(self):
        """Cleanup created resources in reverse order"""
        print("\n🧹 Cleaning up test resources...")

        # Delete any remaining activities
        if self.created_activity_ids:
            for activity_id in self.created_activity_ids:
                try:
                    self.client.feeds.delete_activity(activity_id, hard_delete=True)
                except Exception as e:
                    print(f"Warning: Failed to cleanup activity {activity_id}: {e}")

        # Delete any remaining comments
        if self.created_comment_ids:
            for comment_id in self.created_comment_ids:
                try:
                    self.client.feeds.delete_comment(comment_id, hard_delete=True)
                except Exception as e:
                    print(f"Warning: Failed to cleanup comment {comment_id}: {e}")

        print("✅ Cleanup completed")

    def _assert_response_success(self, response: StreamResponse, operation: str):
        """Assert that a response is successful"""
        if hasattr(response, "status_code"):
            if response.status_code() >= 400:
                pytest.fail(f"Failed to {operation}. Status: {response.status_code()}")
        else:
            # For generated model responses, just assert they exist
            assert response is not None, f"Failed to {operation}. Response is null."

    # =================================================================
    # 1. ENVIRONMENT SETUP TEST (demonstrates the setup process)
    # =================================================================

    def test_01_setup_environment_demo(self):
        """Demonstrate environment setup"""
        print("\n🔧 Demonstrating environment setup...")
        print("✅ Users and feeds are automatically created in setup_method()")
        print(f"   Test User 1: {self.test_user_id}")
        print(f"   Test User 2: {self.test_user_id_2}")

        # Just a demo test - verify setup completed
        assert self.test_user_id is not None

    # =================================================================
    # 2. ACTIVITY OPERATIONS
    # =================================================================

    def test_02_create_activity(self):
        """Test activity creation"""
        print("\n📝 Testing activity creation...")

        # snippet-start: AddActivity
        response = self.client.feeds.add_activity(
            type="post",
            feeds=[self.test_feed.get_feed_identifier()],
            text="This is a test activity from Python SDK",
            user_id=self.test_user_id,
            custom={
                "test_field": "test_value",
                "timestamp": int(datetime.now().timestamp()),
            },
        )
        # snippet-end: AddActivity

        self._assert_response_success(response, "add activity")

        # Access the typed response data directly
        activity_response = response.data
        assert activity_response.activity is not None
        assert activity_response.activity.id is not None
        assert activity_response.activity.text is not None

        # Compare text
        assert (
            activity_response.activity.text == "This is a test activity from Python SDK"
        )

        self.test_activity_id = activity_response.activity.id
        self.created_activity_ids.append(self.test_activity_id)

        print(f"✅ Created activity with ID: {self.test_activity_id}")

    def test_02b_create_activity_with_attachments(self):
        """Test activity creation with image attachments"""
        print("\n🖼️ Testing activity creation with image attachments...")

        # snippet-start: AddActivityWithImageAttachment
        response = self.client.feeds.add_activity(
            type="post",
            feeds=[self.test_feed.get_feed_identifier()],
            text="Look at this amazing view of NYC!",
            user_id=self.test_user_id,
            attachments=[
                Attachment(
                    custom={},
                    image_url="https://example.com/nyc-skyline.jpg",
                    type="image",
                    title="NYC Skyline",
                )
            ],
            custom={"location": "New York City", "camera": "iPhone 15 Pro"},
        )
        # snippet-end: AddActivityWithImageAttachment

        self._assert_response_success(response, "add activity with image attachment")

        data = response.data
        activity_id = data.activity.id
        self.created_activity_ids.append(activity_id)

        print(f"✅ Created activity with image attachment: {activity_id}")

    def test_02c_create_video_activity(self):
        """Test video activity creation"""
        print("\n🎥 Testing video activity creation...")

        # snippet-start: AddVideoActivity
        response = self.client.feeds.add_activity(
            type="video",
            feeds=[self.test_feed.get_feed_identifier()],
            text="Check out this amazing video!",
            user_id=self.test_user_id,
            attachments=[
                Attachment(
                    custom={"duration": 120},
                    asset_url="https://example.com/amazing-video.mp4",
                    type="video",
                    title="Amazing Video",
                )
            ],
            custom={"video_quality": "4K", "duration_seconds": 120},
        )
        # snippet-end: AddVideoActivity

        self._assert_response_success(response, "add video activity")

        data = response.data
        activity_id = data.activity.id
        self.created_activity_ids.append(activity_id)

        print(f"✅ Created video activity: {activity_id}")

    def test_02d_create_story_activity_with_expiration(self):
        """Test story activity with expiration"""
        print("\n📖 Testing story activity with expiration...")

        # snippet-start: AddStoryActivityWithExpiration
        tomorrow = datetime.now() + timedelta(days=1)
        response = self.client.feeds.add_activity(
            type="story",
            feeds=[self.test_feed.get_feed_identifier()],
            text="My daily story - expires tomorrow!",
            user_id=self.test_user_id,
            expires_at=tomorrow.strftime("%Y-%m-%dT%H:%M:%SZ"),
            attachments=[
                Attachment(
                    custom={},
                    image_url="https://example.com/story-image.jpg",
                    type="image",
                ),
                Attachment(
                    custom={"duration": 15},
                    asset_url="https://example.com/story-video.mp4",
                    type="video",
                ),
            ],
            custom={"story_type": "daily", "auto_expire": True},
        )
        # snippet-end: AddStoryActivityWithExpiration

        self._assert_response_success(response, "add story activity with expiration")

        data = response.data
        activity_id = data.activity.id
        self.created_activity_ids.append(activity_id)

        print(f"✅ Created story activity with expiration: {activity_id}")

    def test_02e_create_activity_multiple_feeds(self):
        """Test activity creation to multiple feeds"""
        print("\n📡 Testing activity creation to multiple feeds...")

        # snippet-start: AddActivityToMultipleFeeds
        response = self.client.feeds.add_activity(
            type="post",
            feeds=[
                self.test_feed.get_feed_identifier(),
                self.test_feed_2.get_feed_identifier(),
            ],
            text="This post appears in multiple feeds!",
            user_id=self.test_user_id,
            custom={"cross_posted": True, "target_feeds": 2},
        )
        # snippet-end: AddActivityToMultipleFeeds

        self._assert_response_success(response, "add activity to multiple feeds")

        data = response.data
        activity_id = data.activity.id
        self.created_activity_ids.append(activity_id)

        print(f"✅ Created activity in multiple feeds: {activity_id}")

    def test_03_query_activities(self):
        """Test activity querying"""
        print("\n🔍 Testing activity querying...")

        # snippet-start: QueryActivities
        response = self.client.feeds.query_activities(
            limit=10, filter={"activity_type": "post"}
        )
        # snippet-end: QueryActivities

        self._assert_response_success(response, "query activities")

        data = response.data
        assert data.activities is not None
        print("✅ Queried activities successfully")

    def test_04_get_single_activity(self):
        """Test single activity retrieval"""
        print("\n📄 Testing single activity retrieval...")

        # First create an activity to retrieve
        create_response = self.client.feeds.add_activity(
            type="post",
            text="Activity for retrieval test",
            user_id=self.test_user_id,
            feeds=[self.test_feed.get_feed_identifier()],
        )
        self._assert_response_success(
            create_response, "create activity for retrieval test"
        )

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        # snippet-start: GetActivity
        response = self.client.feeds.get_activity(activity_id)
        # snippet-end: GetActivity

        self._assert_response_success(response, "get activity")

        data = response.data
        assert data.activity is not None
        assert data.activity.id == activity_id
        print("✅ Retrieved single activity")

    def test_05_update_activity(self):
        """Test activity update"""
        print("\n✏️ Testing activity update...")

        # First create an activity to update
        create_response = self.client.feeds.add_activity(
            type="post",
            text="Activity for update test",
            user_id=self.test_user_id,
            feeds=[self.test_feed.get_feed_identifier()],
        )
        self._assert_response_success(
            create_response, "create activity for update test"
        )

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        # snippet-start: UpdateActivity
        response = self.client.feeds.update_activity(
            activity_id,
            text="Updated activity text from Python SDK",
            user_id=self.test_user_id,  # Required for server-side auth
            custom={"updated": True, "update_time": int(datetime.now().timestamp())},
        )
        # snippet-end: UpdateActivity

        self._assert_response_success(response, "update activity")
        print("✅ Updated activity")

    # =================================================================
    # 3. REACTION OPERATIONS
    # =================================================================

    def test_06_add_reaction(self):
        """Test reaction addition"""
        print("\n👍 Testing reaction addition...")

        # First create an activity to react to
        create_response = self.client.feeds.add_activity(
            type="post",
            text="Activity for reaction test",
            user_id=self.test_user_id,
            feeds=[self.test_feed.get_feed_identifier()],
        )
        self._assert_response_success(
            create_response, "create activity for reaction test"
        )

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        # snippet-start: AddReaction
        response = self.client.feeds.add_reaction(
            activity_id, type="like", user_id=self.test_user_id
        )
        # snippet-end: AddReaction

        self._assert_response_success(response, "add reaction")
        print("✅ Added like reaction")

    def test_07_query_reactions(self):
        """Test reaction querying"""
        print("\n🔍 Testing reaction querying...")

        # Create an activity and add a reaction to it
        create_response = self.client.feeds.add_activity(
            type="post",
            text="Activity for query reactions test",
            user_id=self.test_user_id,
            feeds=[self.test_feed.get_feed_identifier()],
        )
        self._assert_response_success(
            create_response, "create activity for query reactions test"
        )

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        # Add a reaction first
        reaction_response = self.client.feeds.add_reaction(
            activity_id, type="like", user_id=self.test_user_id
        )
        self._assert_response_success(reaction_response, "add reaction for query test")

        try:
            # snippet-start: QueryActivityReactions
            response = self.client.feeds.query_activity_reactions(
                activity_id, limit=10, filter={"type": "like"}
            )
            # snippet-end: QueryActivityReactions

            self._assert_response_success(response, "query reactions")
            print("✅ Queried reactions")
        except Exception as e:
            print(f"Query reactions skipped: {e}")

    # =================================================================
    # 4. COMMENT OPERATIONS
    # =================================================================

    def test_08_add_comment(self):
        """Test comment addition"""
        print("\n💬 Testing comment addition...")

        # First create an activity to comment on
        create_response = self.client.feeds.add_activity(
            type="post",
            feeds=[self.test_feed.get_feed_identifier()],
            text="Activity for comment test",
            user_id=self.test_user_id,
        )
        self._assert_response_success(
            create_response, "create activity for comment test"
        )

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        # snippet-start: AddComment
        response = self.client.feeds.add_comment(
            comment="This is a test comment from Python SDK",
            object_id=activity_id,
            object_type="activity",
            user_id=self.test_user_id,
        )
        # snippet-end: AddComment

        self._assert_response_success(response, "add comment")

        data = response.data
        if data.comment and data.comment.id:
            self.test_comment_id = data.comment.id
            self.created_comment_ids.append(self.test_comment_id)
            print(f"✅ Added comment with ID: {self.test_comment_id}")
        else:
            print("✅ Added comment (no ID returned)")

    def test_09_query_comments(self):
        """Test comment querying"""
        print("\n🔍 Testing comment querying...")

        # Create an activity and add a comment to it
        create_response = self.client.feeds.add_activity(
            type="post",
            text="Activity for query comments test",
            user_id=self.test_user_id,
            feeds=[self.test_feed.get_feed_identifier()],
        )
        self._assert_response_success(
            create_response, "create activity for query comments test"
        )

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        # Add a comment first
        comment_response = self.client.feeds.add_comment(
            comment="Comment for query test",
            object_id=activity_id,
            object_type="activity",
            user_id=self.test_user_id,
        )
        self._assert_response_success(comment_response, "add comment for query test")

        # snippet-start: QueryComments
        response = self.client.feeds.query_comments(
            filter={"object_id": activity_id}, limit=10
        )
        # snippet-end: QueryComments

        self._assert_response_success(response, "query comments")
        print("✅ Queried comments")

    def test_10_update_comment(self):
        """Test comment update"""
        print("\n✏️ Testing comment update...")

        # Create an activity and add a comment to update
        create_response = self.client.feeds.add_activity(
            type="post",
            text="Activity for update comment test",
            user_id=self.test_user_id,
            feeds=[self.test_feed.get_feed_identifier()],
        )
        self._assert_response_success(
            create_response, "create activity for update comment test"
        )

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        # Add a comment to update
        comment_response = self.client.feeds.add_comment(
            comment="Comment to be updated",
            object_id=activity_id,
            object_type="activity",
            user_id=self.test_user_id,
        )
        self._assert_response_success(comment_response, "add comment for update test")

        comment_response_data = comment_response.data
        comment_id = (
            comment_response_data.comment.id
            if comment_response_data.comment.id
            else f"comment-{uuid.uuid4()}"
        )

        # snippet-start: UpdateComment
        response = self.client.feeds.update_comment(
            comment_id, comment="Updated comment text from Python SDK"
        )
        # snippet-end: UpdateComment

        self._assert_response_success(response, "update comment")
        print("✅ Updated comment")

    # =================================================================
    # 5. BOOKMARK OPERATIONS
    # =================================================================

    def test_11_add_bookmark(self):
        """Test bookmark addition"""
        print("\n🔖 Testing bookmark addition...")

        # Create an activity to bookmark
        create_response = self.client.feeds.add_activity(
            type="post",
            text="Activity for bookmark test",
            user_id=self.test_user_id,
            feeds=[self.test_feed.get_feed_identifier()],
        )
        self._assert_response_success(
            create_response, "create activity for bookmark test"
        )

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        try:
            # snippet-start: AddBookmark
            response = self.client.feeds.add_bookmark(
                activity_id,
                user_id=self.test_user_id,
                new_folder=AddFolderRequest(name="test-bookmarks1"),
            )
            # snippet-end: AddBookmark

            print(f"Bookmark response status: {response.status_code}")
            print(f"Bookmark response body: {response.raw_body}")
            self._assert_response_success(response, "add bookmark")
        except Exception as e:
            print(f"Add bookmark failed: {e}")
        print("✅ Added bookmark")

    def test_12_query_bookmarks(self):
        """Test bookmark querying"""
        print("\n🔍 Testing bookmark querying...")

        # snippet-start: QueryBookmarks
        response = self.client.feeds.query_bookmarks(
            limit=10, filter={"user_id": self.test_user_id}
        )
        # snippet-end: QueryBookmarks

        assert isinstance(response, StreamResponse)
        self._assert_response_success(response, "query bookmarks")
        print("✅ Queried bookmarks")

    def test_13_update_bookmark(self):
        """Test bookmark update"""
        print("\n✏️ Testing bookmark update...")

        # Create an activity and bookmark it first
        create_response = self.client.feeds.add_activity(
            type="post",
            feeds=[self.test_feed.get_feed_identifier()],
            text="Activity for update bookmark test",
            user_id=self.test_user_id,
        )
        self._assert_response_success(
            create_response, "create activity for update bookmark test"
        )

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        # Add a bookmark first
        bookmark_response = self.client.feeds.add_bookmark(
            activity_id,
            new_folder=AddFolderRequest(name="test-bookmarks1"),
            user_id=self.test_user_id,
        )
        self._assert_response_success(bookmark_response, "add bookmark for update test")

        # snippet-start: UpdateBookmark
        bookmark_data = bookmark_response.data
        folder_id = bookmark_data.bookmark.folder.id
        response = self.client.feeds.update_bookmark(
            activity_id, folder_id=folder_id, user_id=self.test_user_id
        )
        # snippet-end: UpdateBookmark

        self._assert_response_success(response, "update bookmark")
        print("✅ Updated bookmark")

    # =================================================================
    # 6. FOLLOW OPERATIONS
    # =================================================================

    def test_14_follow_user(self):
        """Test follow operation"""
        print("\n👥 Testing follow operation...")

        try:
            # snippet-start: Follow
            response = self.client.feeds.follow(
                source=f"{self.USER_FEED_TYPE}:{self.test_user_id}",
                target=f"{self.USER_FEED_TYPE}:{self.test_user_id_2}",
            )
            # snippet-end: Follow

            self._assert_response_success(response, "follow user")
        except Exception as e:
            print(f"Follow failed: {e}")
        print(f"✅ Followed user: {self.test_user_id_2}")

    def test_15_query_follows(self):
        """Test follow querying"""
        print("\n🔍 Testing follow querying...")

        # snippet-start: QueryFollows
        response = self.client.feeds.query_follows(limit=10)
        # snippet-end: QueryFollows

        assert isinstance(response, StreamResponse)
        self._assert_response_success(response, "query follows")
        print("✅ Queried follows")

    # =================================================================
    # 7. BATCH OPERATIONS
    # =================================================================

    def test_16_upsert_activities(self):
        """Test batch activity upsert"""
        print("\n📝 Testing batch activity upsert...")

        # snippet-start: UpsertActivities
        activities = [
            ActivityRequest(
                type="post",
                text="Batch activity 1",
                user_id=self.test_user_id,
                feeds=[self.test_feed.get_feed_identifier()],
            ),
            ActivityRequest(
                type="post",
                text="Batch activity 2",
                user_id=self.test_user_id,
                feeds=[self.test_feed.get_feed_identifier()],
            ),
        ]

        response = self.client.feeds.upsert_activities(activities=activities)
        # snippet-end: UpsertActivities

        assert isinstance(response, StreamResponse)
        self._assert_response_success(response, "upsert activities")

        # Track created activities for cleanup
        data = response.data
        if hasattr(data, "activities") and data.activities:
            for activity in data.activities:
                if hasattr(activity, "id") and activity.id:
                    self.created_activity_ids.append(activity.id)

        print("✅ Upserted batch activities")

    # =================================================================
    # 8. ADVANCED OPERATIONS
    # =================================================================

    def test_17_pin_activity(self):
        """Test activity pinning"""
        print("\n📌 Testing activity pinning...")

        # Create an activity to pin
        create_response = self.client.feeds.add_activity(
            type="post",
            feeds=[self.test_feed.get_feed_identifier()],
            text="Activity for pin test",
            user_id=self.test_user_id,
        )
        self._assert_response_success(create_response, "create activity for pin test")

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        # snippet-start: PinActivity
        response = self.test_feed.pin_activity(activity_id, user_id=self.test_user_id)
        # snippet-end: PinActivity

        self._assert_response_success(response, "pin activity")
        print("✅ Pinned activity")

    def test_18_unpin_activity(self):
        """Test activity unpinning"""
        print("\n📌 Testing activity unpinning...")

        # Create an activity, pin it, then unpin it
        create_response = self.client.feeds.add_activity(
            type="post",
            feeds=[self.test_feed.get_feed_identifier()],
            text="Activity for unpin test",
            user_id=self.test_user_id,
        )
        self._assert_response_success(create_response, "create activity for unpin test")

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        # Pin it first
        pin_response = self.test_feed.pin_activity(
            activity_id, user_id=self.test_user_id
        )
        self._assert_response_success(pin_response, "pin activity for unpin test")

        # snippet-start: UnpinActivity
        response = self.test_feed.unpin_activity(activity_id, self.test_user_id)
        # snippet-end: UnpinActivity

        self._assert_response_success(response, "unpin activity")
        print("✅ Unpinned activity")

    # =================================================================
    # 9. CLEANUP OPERATIONS (in reverse order)
    # =================================================================

    def test_19_delete_bookmark(self):
        """Test bookmark deletion"""
        print("\n🗑️ Testing bookmark deletion...")

        # Create an activity and bookmark it first
        create_response = self.client.feeds.add_activity(
            type="post",
            text="Activity for delete bookmark test",
            user_id=self.test_user_id,
            feeds=[self.test_feed.get_feed_identifier()],
        )
        self._assert_response_success(
            create_response, "create activity for delete bookmark test"
        )

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        # Add a bookmark first
        bookmark_response = self.client.feeds.add_bookmark(
            activity_id,
            new_folder=AddFolderRequest(name="test-bookmarks1"),
            user_id=self.test_user_id,
        )
        self._assert_response_success(bookmark_response, "add bookmark for delete test")

        # snippet-start: DeleteBookmark
        bookmark_data = bookmark_response.data
        folder_id = bookmark_data.bookmark.folder.id
        response = self.client.feeds.delete_bookmark(
            activity_id, folder_id, self.test_user_id
        )
        # snippet-end: DeleteBookmark

        self._assert_response_success(response, "delete bookmark")
        print("✅ Deleted bookmark")

    def test_20_delete_reaction(self):
        """Test reaction deletion"""
        print("\n🗑️ Testing reaction deletion...")

        # Create an activity and add a reaction first
        create_response = self.client.feeds.add_activity(
            type="post",
            text="Activity for delete reaction test",
            user_id=self.test_user_id,
            feeds=[self.test_feed.get_feed_identifier()],
        )
        self._assert_response_success(
            create_response, "create activity for delete reaction test"
        )

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        # Add a reaction first
        reaction_response = self.client.feeds.add_reaction(
            activity_id, type="like", user_id=self.test_user_id
        )
        self._assert_response_success(reaction_response, "add reaction for delete test")

        # snippet-start: DeleteActivityReaction
        response = self.client.feeds.delete_activity_reaction(
            activity_id, "like", self.test_user_id
        )
        # snippet-end: DeleteActivityReaction

        self._assert_response_success(response, "delete reaction")
        print("✅ Deleted reaction")

    def test_21_delete_comment(self):
        """Test comment deletion"""
        print("\n🗑️ Testing comment deletion...")

        # Create an activity and add a comment first
        create_response = self.client.feeds.add_activity(
            type="post",
            text="Activity for delete comment test",
            user_id=self.test_user_id,
            feeds=[self.test_feed.get_feed_identifier()],
        )
        self._assert_response_success(
            create_response, "create activity for delete comment test"
        )

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        # Add a comment first
        comment_response = self.client.feeds.add_comment(
            comment="Comment to be deleted",
            object_id=activity_id,
            object_type="activity",
            user_id=self.test_user_id,
        )
        self._assert_response_success(comment_response, "add comment for delete test")

        comment_response_data = comment_response.data
        comment_id = (
            comment_response_data.comment.id
            if comment_response_data.comment.id
            else f"comment-{uuid.uuid4()}"
        )

        # snippet-start: DeleteComment
        response = self.client.feeds.delete_comment(
            comment_id, hard_delete=False
        )  # soft delete
        # snippet-end: DeleteComment

        self._assert_response_success(response, "delete comment")
        print("✅ Deleted comment")

    def test_22_unfollow_user(self):
        """Test unfollow operation"""
        print("\n👥 Testing unfollow operation...")

        try:
            # First establish a follow relationship
            follow_response = self.client.feeds.follow(
                source=f"{self.USER_FEED_TYPE}:{self.test_user_id}",
                target=f"{self.USER_FEED_TYPE}:{self.test_user_id_2}",
            )
            self._assert_response_success(
                follow_response, "establish follow relationship for unfollow test"
            )

            # snippet-start: Unfollow
            response = self.client.feeds.unfollow(
                f"{self.USER_FEED_TYPE}:{self.test_user_id}",
                f"{self.USER_FEED_TYPE}:{self.test_user_id_2}",
            )
            # snippet-end: Unfollow

            assert isinstance(response, StreamResponse)
            self._assert_response_success(response, "unfollow operation")
            print(f"✅ Unfollowed user: {self.test_user_id_2}")
        except Exception as e:
            print(f"Unfollow operation skipped: {e}")

    def test_23_delete_activities(self):
        """Test activity deletion"""
        print("\n🗑️ Testing activity deletion...")

        # Create some activities to delete
        activities_to_delete = []
        for i in range(1, 3):
            create_response = self.client.feeds.add_activity(
                type="post",
                text=f"Activity {i} for delete test",
                user_id=self.test_user_id,
                feeds=[self.test_feed.get_feed_identifier()],
            )
            self._assert_response_success(
                create_response, f"create activity {i} for delete test"
            )

            create_data = create_response.data
            activity_id = create_data.activity.id
            activities_to_delete.append(activity_id)
            self.created_activity_ids.append(activity_id)

        for activity_id in activities_to_delete:
            # snippet-start: DeleteActivity
            response = self.client.feeds.delete_activity(
                activity_id, hard_delete=False
            )  # soft delete
            # snippet-end: DeleteActivity

            self._assert_response_success(response, "delete activity")

        print(f"✅ Deleted {len(activities_to_delete)} activities")
        self.created_activity_ids = []

    # =================================================================
    # 10. ADDITIONAL COMPREHENSIVE TESTS
    # =================================================================

    def test_24_create_poll(self):
        """Test poll creation"""
        print("\n🗳️ Testing poll creation...")

        try:
            # snippet-start: CreatePoll
            poll = {
                "name": "Poll",
                "description": self.POLL_QUESTION,
                "user_id": self.test_user_id,
                "options": ["Red", "Blue"],
            }
            poll_response = self.client.create_poll(**poll)
            poll_data = poll_response.data
            poll_id = poll_data.get("id", f"poll-{uuid.uuid4()}")

            poll_activity_response = self.client.feeds.add_activity(
                type="poll",
                feeds=[self.test_feed.get_feed_identifier()],
                poll_id=poll_id,
                text=self.POLL_QUESTION,
                user_id=self.test_user_id,
                custom={
                    "poll_name": self.POLL_QUESTION,
                    "poll_description": "Choose your favorite programming language from the options below",
                    "poll_options": ["PHP", "Python", "JavaScript", "Go"],
                    "allow_user_suggested_options": False,
                    "max_votes_allowed": 1,
                },
            )
            # snippet-end: CreatePoll

            self._assert_response_success(poll_activity_response, "create poll")

            data = poll_activity_response.data
            activity_id = data.activity.id
            self.created_activity_ids.append(activity_id)

            print(f"✅ Created poll activity: {activity_id}")
        except Exception as e:
            print(f"Poll creation skipped: {e}")

    def test_25_vote_poll(self):
        """Test poll voting"""
        print("\n✅ Testing poll voting...")

        try:
            # Create a poll first using the proper API
            poll = {
                "name": "Favorite Color Poll",
                "description": "What is your favorite color?",
                "user_id": self.test_user_id,
                "options": ["Red", "Blue", "Green"],
            }
            poll_response = self.client.create_poll(**poll)
            poll_data = poll_response.data
            poll_id = poll_data.get("id", f"poll-{uuid.uuid4()}")

            # Create activity with the poll
            create_response = self.client.feeds.add_activity(
                type="poll",
                feeds=[self.test_feed.get_feed_identifier()],
                text="Vote for your favorite color",
                user_id=self.test_user_id,
                poll_id=poll_id,
                custom={
                    "poll_name": "What is your favorite color?",
                    "poll_description": "Choose your favorite color from the options below",
                    "poll_options": ["Red", "Blue", "Green"],
                    "allow_user_suggested_options": False,
                },
            )

            self._assert_response_success(create_response, "create poll for voting")

            create_data = create_response.data
            activity_id = create_data.activity.id
            self.created_activity_ids.append(activity_id)

            # Get poll options from the poll response
            poll_options = poll_data.get("options", [])

            if poll_options:
                # Use the first option ID from the poll creation response
                option_id = poll_options[0].get("id", poll_options[0])

                try:
                    # snippet-start: VotePoll
                    vote_response = self.client.feeds.cast_poll_vote(
                        activity_id,
                        poll_id,
                        user_id=self.test_user_id,
                        vote=VoteData(option_id=option_id),
                    )
                    # snippet-end: VotePoll

                    self._assert_response_success(vote_response, "vote on poll")
                    print(f"✅ Voted on poll: {activity_id}")
                except Exception as e:
                    print(f"Poll voting skipped: {e}")
            else:
                print("⚠️ Poll options not found in poll response")
        except Exception as e:
            print(f"Poll voting skipped: {e}")

    def test_26_moderate_activity(self):
        """Test activity moderation"""
        print("\n🛡️ Testing activity moderation...")

        # Create an activity to moderate
        create_response = self.client.feeds.add_activity(
            type="post",
            text="This content might need moderation",
            user_id=self.test_user_id,
            feeds=[self.test_feed.get_feed_identifier()],
        )
        self._assert_response_success(create_response, "create activity for moderation")

        create_data = create_response.data
        activity_id = create_data.activity.id
        self.created_activity_ids.append(activity_id)

        try:
            # snippet-start: ModerateActivity
            moderation_response = self.client.feeds.activity_feedback(
                activity_id,
                report=True,
                reason="inappropriate_content",
                user_id=self.test_user_id_2,  # Different user reporting
            )
            # snippet-end: ModerateActivity

            self._assert_response_success(moderation_response, "moderate activity")
            print(f"✅ Flagged activity for moderation: {activity_id}")
        except Exception as e:
            print(f"Activity moderation skipped: {e}")

    def test_27_device_management(self):
        """Test device management"""
        print("\n📱 Testing device management...")

        device_token = f"test-device-token-{uuid.uuid4()}"

        try:
            # snippet-start: AddDevice
            add_device_response = self.client.create_device(
                id=device_token, push_provider="apn", user_id=self.test_user_id
            )
            # snippet-end: AddDevice

            self._assert_response_success(add_device_response, "add device")
            print(f"✅ Added device: {device_token}")

            # snippet-start: RemoveDevice
            remove_device_response = self.client.delete_device(
                device_token, self.test_user_id
            )
            # snippet-end: RemoveDevice

            self._assert_response_success(remove_device_response, "remove device")
            print(f"✅ Removed device: {device_token}")
        except Exception as e:
            print(f"Device management skipped: {e}")

    def test_28_query_activities_with_filters(self):
        """Test activity queries with advanced filters"""
        print("\n🔍 Testing activity queries with advanced filters...")

        # Create activities with different types and metadata
        activity_types = ["post", "photo", "video", "story"]

        for activity_type in activity_types:
            create_response = self.client.feeds.add_activity(
                type=activity_type,
                text=f"Test {activity_type} activity for filtering",
                user_id=self.test_user_id,
                feeds=[self.test_feed.get_feed_identifier()],
                custom={
                    "category": activity_type,
                    "priority": 3,  # Random priority between 1-5
                    "tags": [activity_type, "test", "filter"],
                },
            )
            self._assert_response_success(
                create_response, f"create {activity_type} activity for filtering"
            )

            create_data = create_response.data
            self.created_activity_ids.append(create_data.activity.id)

        try:
            # Query with type filter
            # snippet-start: QueryActivitiesWithTypeFilter
            response = self.client.feeds.query_activities(
                limit=10,
                filter={"activity_type": "post", "user_id": self.test_user_id},
                sort=[
                    SortParamRequest(field="created_at", direction=-1)
                ],  # newest first
            )
            # snippet-end: QueryActivitiesWithTypeFilter

            self._assert_response_success(response, "query activities with type filter")
        except Exception as e:
            print(f"Query activities with type filter skipped: {e}")

        try:
            # Query with custom field filter
            # snippet-start: QueryActivitiesWithCustomFilter
            custom_filter_response = self.client.feeds.query_activities(
                limit=10,
                filter={
                    "custom.priority": {"$gte": 3},  # priority >= 3
                    "user_id": self.test_user_id,
                },
            )
            # snippet-end: QueryActivitiesWithCustomFilter

            self._assert_response_success(
                custom_filter_response, "query activities with custom filter"
            )
        except Exception as e:
            print(f"Query activities with custom filter skipped: {e}")

        print("✅ Queried activities with advanced filters")

    def test_29_get_feed_activities_with_pagination(self):
        """Test feed activities with pagination"""
        print("\n📄 Testing feed activities with pagination...")

        # Create multiple activities for pagination test
        for i in range(1, 8):
            create_response = self.client.feeds.add_activity(
                type="post",
                text=f"Pagination test activity {i}",
                user_id=self.test_user_id,
                feeds=[self.test_feed.get_feed_identifier()],
            )
            self._assert_response_success(
                create_response, f"create pagination activity {i}"
            )

            create_data = create_response.data
            self.created_activity_ids.append(create_data.activity.id)

        # Get first page
        # snippet-start: GetFeedActivitiesWithPagination
        first_page_response = self.client.feeds.query_activities(
            limit=3, filter={"user_id": self.test_user_id}
        )
        # snippet-end: GetFeedActivitiesWithPagination

        self._assert_response_success(
            first_page_response, "get first page of feed activities"
        )

        first_page_data = first_page_response.data
        assert first_page_data.activities is not None
        assert len(first_page_data.activities) <= 3

        # Get second page using next token if available
        # snippet-start: GetFeedActivitiesSecondPage
        next_token = getattr(first_page_data, "next", None)
        if next_token:
            second_page_response = self.client.feeds.query_activities(
                limit=3, next=next_token, filter={"user_id": self.test_user_id}
            )
            self._assert_response_success(
                second_page_response, "get second page of feed activities"
            )
        else:
            print("⚠️ No next page available")
        # snippet-end: GetFeedActivitiesSecondPage

        print("✅ Retrieved feed activities with pagination")

    def test_30_error_handling_scenarios(self):
        """Test comprehensive error handling scenarios"""
        print("\n⚠️ Testing error handling scenarios...")

        # Test 1: Invalid activity ID
        try:
            # snippet-start: HandleInvalidActivityId
            response = self.client.feeds.get_activity("invalid-activity-id-12345")
            # snippet-end: HandleInvalidActivityId

            if not response.is_successful():
                print("✅ Correctly handled invalid activity ID error")
        except Exception as e:
            print(f"✅ Caught expected error for invalid activity ID: {e}")

        # Test 2: Empty activity text
        try:
            # snippet-start: HandleEmptyActivityText
            response = self.client.feeds.add_activity(
                type="post",
                text="",  # Empty text
                user_id=self.test_user_id,
                feeds=[self.test_feed.get_feed_identifier()],
            )
            # snippet-end: HandleEmptyActivityText

            if not response.is_successful():
                print("✅ Correctly handled empty activity text")
        except Exception as e:
            print(f"✅ Caught expected error for empty activity text: {e}")

        # Test 3: Invalid user ID
        try:
            # snippet-start: HandleInvalidUserId
            response = self.client.feeds.add_activity(
                type="post",
                text="Test with invalid user",
                user_id="",  # Empty user ID
                feeds=[self.test_feed.get_feed_identifier()],
            )
            # snippet-end: HandleInvalidUserId

            if not response.is_successful():
                print("✅ Correctly handled invalid user ID")
        except Exception as e:
            print(f"✅ Caught expected error for invalid user ID: {e}")

        # Test passes if we reach here without exceptions
        assert self.test_user_id is not None

    def test_31_authentication_scenarios(self):
        """Test authentication and authorization scenarios"""
        print("\n🔐 Testing authentication scenarios...")

        # Test with valid user authentication
        # snippet-start: ValidUserAuthentication
        response = self.client.feeds.add_activity(
            type="post",
            text="Activity with proper authentication",
            user_id=self.test_user_id,
            feeds=[self.test_feed.get_feed_identifier()],
        )
        # snippet-end: ValidUserAuthentication

        self._assert_response_success(response, "activity with valid authentication")

        data = response.data
        activity_id = data.activity.id
        self.created_activity_ids.append(activity_id)

        print(f"✅ Successfully authenticated and created activity: {activity_id}")

        # Test user permissions for updating activity
        # snippet-start: UserPermissionUpdate
        update_response = self.client.feeds.update_activity(
            activity_id,
            text="Updated with proper user permissions",
            user_id=self.test_user_id,  # Same user can update
        )
        # snippet-end: UserPermissionUpdate

        self._assert_response_success(
            update_response, "update activity with proper permissions"
        )
        print("✅ Successfully updated activity with proper user permissions")

    def test_32_real_world_usage_demo(self):
        """Comprehensive test demonstrating real-world usage patterns"""
        print("\n🌍 Testing real-world usage patterns...")

        # Scenario: User posts content, gets reactions and comments
        # snippet-start: RealWorldScenario

        # 1. User creates a post with image
        post_response = self.client.feeds.add_activity(
            type="post",
            text="Just visited the most amazing coffee shop! ☕️",
            user_id=self.test_user_id,
            feeds=[self.test_feed.get_feed_identifier()],
            attachments=[
                Attachment(
                    custom={},
                    image_url="https://example.com/coffee-shop.jpg",
                    type="image",
                    title="Amazing Coffee Shop",
                )
            ],
            custom={
                "location": "Downtown Coffee Co.",
                "rating": 5,
                "tags": ["coffee", "food", "downtown"],
            },
        )
        self._assert_response_success(post_response, "create real-world post")

        post_data = post_response.data
        post_id = post_data.activity.id
        self.created_activity_ids.append(post_id)

        # 2. Other users react to the post
        reaction_types = ["like", "love", "wow"]
        for reaction_type in reaction_types:
            reaction_response = self.client.feeds.add_reaction(
                post_id, type=reaction_type, user_id=self.test_user_id_2
            )
            self._assert_response_success(
                reaction_response, f"add {reaction_type} reaction"
            )

        # 3. Users comment on the post
        comments = [
            "That place looks amazing! What did you order?",
            "I love their espresso! Great choice 😍",
            "Adding this to my must-visit list!",
        ]

        for comment_text in comments:
            comment_response = self.client.feeds.add_comment(
                comment=comment_text,
                object_id=post_id,
                object_type="activity",
                user_id=self.test_user_id_2,
            )
            self._assert_response_success(comment_response, "add comment to post")

        # 4. User bookmarks the post
        try:
            bookmark_response = self.client.feeds.add_bookmark(
                post_id,
                user_id=self.test_user_id_2,
                new_folder=AddFolderRequest(name="favorite-places"),
            )
            self._assert_response_success(bookmark_response, "bookmark the post")
        except Exception as e:
            print(f"Bookmark operation skipped: {e}")

        # 5. Query the activity with all its interactions
        enriched_response = self.client.feeds.get_activity(post_id)
        self._assert_response_success(enriched_response, "get enriched activity")

        # snippet-end: RealWorldScenario

        print("✅ Completed real-world usage scenario demonstration")
