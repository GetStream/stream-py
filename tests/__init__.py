from stream.sync import Stream

client = Stream(
    api_key="your-api-key",
    api_secret="your-api-secret",
)

print(
    client.create_token(
        user_id="admin-user", role="admin", call_cids=["default:8PNZC9qq3A1V"]
    )
)
# for some reason I'm still getting 500s
print(client.video.edges())
