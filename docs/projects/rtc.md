## Step 1 - Create very basic python example RTC test

Create a python test file that we will use for all RTC tests and add a first very basic test function

The test should do this work like this:

1. initialize the video SDK
2. initialize a call object using the client.rtc_call method
3. Use these credentials to initialize the SDK key "hd8szvscpxvd" and secret "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWktcmVjb3JkZXIifQ.Ic1dVrjX_gbfb4IdO9lhvZteQi8Ki_w0AlCXUvwot8k"

There is not much to test in this case so just run the test with a few seconds timeout

## Step 2 - Expand the JoinCall signature in Go with API credentials

In this step you need to change the exported JoinCall function to have the api key and secret parameter, python code will also need to be adjusted. Make sure to adjust the echo test.

## Step 3 - Test for wrong credentials exception

When initialized with bad credentials, joining a call should raise an exception. Go needs to signal this to python using the callback function. Ideally the python code looks like this:

```python
call = client.video.rtc_call("default", "example-ai-recorder")
call.get_or_create(data=CallRequest(created_by_id="ai-recorder"))
await call.join("ai-recorder")
```

where await call.join("ai-recorder") will return the first event sent by Go and if that event is an error event it will raise an exception
