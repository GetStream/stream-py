## Step 1 - Create very basic python example RTC test

Create a python test file that we will use for all RTC tests and add a first very basic test function

The test should do this work like this:

1. initialize the video SDK
2. initialize a call object using the client.rtc_call method
3. Use these credentials to initialize the SDK key "hd8szvscpxvd" and secret "4dv9yu4hqy7xvqk35vpbnqrafg2b43rzu8u4wt93mgrc3cd2ufb5bndb73g58emq"

There is not much to test in this case so just run the test with a few seconds timeout

## Step 2 - Expand the JoinCall signature in Go with API credentials

In this step you need to change the exported JoinCall function to have the api key and secret parameter, python code will also need to be adjusted. Make sure to adjust the echo test.

## Step 3 - make call.join an async function that can throw

Make sure to follow instructions in @ai-basic @ai-testing and @ai-codegen files. You need to adjust the Python SDK and make the join method an async method that can throw if joining the call fails for any reason (eg. server errors, bad auth, ...).

```python
call = client.video.rtc_call("default", "example-ai-recorder")
call.get_or_create(data=CallRequest(created_by_id="ai-recorder"))

# this throws or block until the call is finished
async call.join("ai-recorder")
```

Let's adjust the go code a bit so this way:

- if joining the call fails with an error, send an error event to the callback function
- if joining the call succeeds, it sends a CallJoinResponse event to the callback function

Both Error and CallJoinResponse types need to be added to the events.proto file and added as oneofs there.

The Error message should be flexible enough so that we can easily use it for more errors in the future. eg. in this case the error is related to joining the call so ideally we have a code for that. The error message from go should also be included as a error message string field.

The CallJoinResponse can be for now an empty message with no fields.

On the python side: the join function will be an async function that waits for the first event to arrive. If the first event is an error message then it throws an exception containing the error message. The exception should use the message field in its representation so its easy to see what happened.

Make sure to create two tests:

One test should connects to the call using the client for fixtures, because the code is blocking you need to add a timeout.
The other test, should initialize another client with invalid credentials, join a call and be expected to throw an exception

## Step 4 - Change call.join to be an something that can be used like this:


```python
call = client.video.rtc_call("default", "example-ai-recorder")
call.get_or_create(data=CallRequest(created_by_id="ai-recorder"))

async with call.join("ai-recorder") as connection:
    async for event in connection:
        pass
```

so call.join should become an async function that returns a connection manager, the connection can be iterated and it will yield events coming from Go via the callback function that Python sends to Go via cffi

## Step 4 - Change call.join to be an something that can be used like this:


```python
call = client.video.rtc_call("default", "example-ai-recorder")
call.get_or_create(data=CallRequest(created_by_id="ai-recorder"))

async with call.join("ai-recorder") as connection:
    async for event in connection:
        pass
```

so call.join should become an async function that returns a connection manager, the connection can be iterated and it will yield events coming from Go via the callback function that Python sends to Go via cffi

## Step 5 - API to receive audio packets

Continuing on step 3, let's create a function to receive audio events from a connection

```python
call = client.video.rtc_call("default", "example-ai-recorder")
call.get_or_create(data=CallRequest(created_by_id="ai-recorder"))

async with call.join("ai-recorder") as connection:
    async for participant, audio in connection.incoming_audio:
        pass

```

Where the yielded values are:

participant: the id of the user sending the audio
audio: tuple[int, np.ndarray] a tuple containing sample rate and pcm samples as np.int16

On the Go side, we need to ensure that incoming audio RTP packets are sent and converted from opus to int16 pcm samples with 48000 rate. This then needs to be sent as a RTCPacket.AudioPayload.PCMAudioPayload proto message

When this is done, create a simple test that connects to the call and prints each time an audio event is received
