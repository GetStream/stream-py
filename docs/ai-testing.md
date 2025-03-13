Python tests:

When writing a python test, follow these rules:

1. Do not mock things unless you are directly asked to do that
2. Do not create 1 file for each test, better if we use 1 test file per topic (eg. test_rtc.py)
3. Test should run using uv and pytest
4. All tests live under the tests/ folder
5. Try to reuse code when possible, there is a conftest file with fixtures where you can put helpers or re-use existing ones
6. If you need a client, use the fixture and it will get you a client loaded from .env
7. Sometime you need to create the client object (eg. use a client with wrong credentials), in that case you can use Stream(api_key="your_api_key", api_secret="your_api_secret") directly
8. Some tests need to be async, make sure to use the pytest decorator for that
9. When you initialize a call object, you need to pass two params: type and id. Type should always be "default" and an arbitrary string like a uuidv4 string

This is a good example of python test:

```python
@pytest.mark.asyncio
async def test_rtc_call_initialization(client):
    # uses the client from fixture and create an rtc_call object
    call = client.video.call("default", "123")

    # this is supposed to resolve and not throw
    await call.join()
```
