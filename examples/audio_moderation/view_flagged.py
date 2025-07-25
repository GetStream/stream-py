from getstream import Stream
from dotenv import load_dotenv
from getstream.models import QueryReviewQueueResponse, ReviewQueueItemResponse

load_dotenv()


if __name__ == "__main__":
    client = Stream.from_env()

    response: QueryReviewQueueResponse = client.moderation.query_review_queue().data
    item: ReviewQueueItemResponse
    for item in response.items:
        print("--------------------------------")
        print(f"Flagged audio transcript with ID: {item.id}")
        if item.moderation_payload is not None:
            print(f"Transcript: {item.moderation_payload.texts[0]}")
        else:
            print("No transcript available")
        print(f"Created at: {item.created_at.isoformat()}")
        print(f"Status: {item.status}")
        print(f"Recommended action: {item.recommended_action}")
