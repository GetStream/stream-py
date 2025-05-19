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


## Step 4 - pass call type and call id from the RTC call object to Go

Atm Go has call type and id hard coded in call, err := sdk.JoinCall(context.Background(), "default", "example-ai-recorder", models.JoinCallRequest{})

Instead, we should have these parameters to be passed down from python to go via cffi

## Step 5 - Change call.join to be an something that can be used like this:

Make sure to follow instructions in @ai-basic and @ai-testing.

```python
call = client.video.rtc_call("default", "example-ai-recorder")
call.get_or_create(data=CallRequest(created_by_id="ai-recorder"))

async with call.join("ai-recorder") as connection:
    async for event in connection:
        pass
```

so call.join should become an async function that returns a connection manager, the connection can be iterated and it will yield events coming from Go via the callback function that Python sends to Go via cffi.

Make sure to run all tests in test_rtc and adjust them if necessary, also make sure to have a test (not necessarily a new one) that loops for events over the connection and prints the first one.

## Step 4 - Change call.join to be an something that can be used like this:


```python
call = client.video.rtc_call("default", "example-ai-recorder")

async with call.join("ai-recorder") as connection:
    async for event in connection:
        pass
```

so call.join should become an async function that returns a connection manager, the connection can be iterated and it will yield events coming from Go via the callback function that Python sends to Go via cffi

## Step 6 - Mock audio events

In this step, we are going to create a mock for a real call. The mock should live in Go so that we test the entire flow with protobuf events but we skip the entire API / webRTC layer.

The result should be something that allows python to inject the desired behavior to the Go mock. To make things easier, create a mock configuration  type in protobuf so that python and go can have a nice structured type to define what the mock should do.

For now I want to support this:

- Which participants (id, name) should be in the call
- The audio files to read and pass as audio events (by participant)

It should be possible to tell go to send audio events at a realistic pace (eg. 20ms audio pcm every 20ms) or to send audio events as fast as they are read from files.

On the python side, activating the mock should be something that you can do at the RTCCall object level before joining the call.
On the Go side, when python wants a mocked call, we will receive a mockedConfig argument and use a mock instead of the regular flow as we do now.

Audio events should contain real audio pcm data coming from different file formats. Depending on the file format, Go should ensure to load the file, convert it to a stream of PCM data and send 1 event with 20ms of audio data. If requested, each track should emit 20ms audio every 20ms.

You can use ffmpeg with pipes to convert file from their original format (eg. mp3) to PCM.

For now, only support the .wav format, we will add support for other formats later. Make sure to write a python test that loads the file from /Users/tommaso/src/data-samples/audio/king_story_1.wav. The test should that ensures the right amount of events are received. The new test should live in the existing test_rtc file.

Change the Join c-function to include the mock config parameter, when provided the mock flow should be used instead of the real join call flow.

After changing the main.go file, you will need to regenerate the go code to run the test, that's done by following the instructions about code generation.

## Step 7 - API to receive audio packets

@ai-basic.md @ai-codegen.md @ai-testing.md extend the connection manager so that one can interate over incoming audio events only

something like this

```
async with call.join("ai-recorder") as connection:
    async for participant, audio in connection.incoming_audio:
        pass

```

At the moment we have a utility function in @test_rtc.py called has_audio_support that would be replaced by the new .incoming_audio API

The yielded values are:

participant: the id of the user sending the audio
audio: tuple[int, np.ndarray] a tuple containing sample rate and pcm samples as np.int16

On the Go side, we need to ensure that incoming audio RTP packets are sent and converted from opus to int16 pcm samples with 48000 rate. This then needs to be sent as a RTCPacket.AudioPayload.PCMAudioPayload proto message

Adjust test all existing tests dealing with audio events.

## Step 7 - exit call

@ai-codegen.md @ai-testing.md @ai-basic.md I want to be sure that the connection manager ends when the call is finished. This should be the logic

- on the go side @main.go when using a mock the call will end when all participant audio is sent
- @main.go should send a "call ended" event to python when the call is finished (in case of a mock, that happens when all audio is sent)
- on the python side, the connection manager should exit when the call ended event is received

write a simple new test to ensure that on a mocked call, python will receive such event and that the connection manager will exit

## Step 8 - leaving call from python

Add a .leave method to the connection manager that will signal Go to exit the call. Study the main.go file to see how the Join works

## Step 9 - refactor code

@main.go  @ai-basic.md @ai-codegen.md @ai-testing.md   create a new package called handler under bindings, organize the two handlers code in this package using two different files. Make sure that the header definition is organized correctly without duplicating code.

The main.go should only act as the entry point and delegate to handler all the actual implementation. Because some types are defined with C, you will need to extract them in a header file and import that one in the relevant files.

Make sure to not change the external C API surface, this change should require no modification on the Python side because it is only a refactoring.

make sure to run the python test_call_ended_event_sent_from_go test before starting the work and after the changes. This way you can see that things work before the refactoring and afterwards.


## Step 10 - Use ffmpeg to send audio

Adjust the mock handler in Go so that the conversion from mp3 and wav to PCM follows this rules:

- it resamples audio to 48000 hz
- it sends 2 channels
- it encodes data using int16
- use ffmpeg to covert the audio file to the target format, use pipes
- each audio event should have up to 20ms of audio
- if the mock is instructed to receive audio in realtime, emit audio events every 20ms (ticker)
- for both mp3 and wav, make sure to create go unit tests to ensure we convert from file to audio events correctly (eg. how many events, how many samples in total)
- audio events should populate the AudioPayload payload correctly (PCMAudioPayload, format, sample rate, ...)

These changes should not change anything on the C API

## Step 11 - Realtime transcriptions

create an example application under examples/video and create one initial example app in python that does the following:

1. it launches an aynsc main function
2. the async main function creates a mock call and uses the jfk audio example as used in @test_rtc.py
3. it uses OpenAI Realtime API to perform transcriptions of the incoming audio events
4. it gets the OpenAI credentials from the .env file at the root of the project
5. it prints all events coming from OpenAI

as a reference, here some relevant examples from their docs:

@https://platform.openai.com/docs/guides/realtime?use-case=transcription&connection-example=python#connect-with-websockets

as well as

@https://platform.openai.com/docs/guides/realtime-transcription#handling-transcriptions

the example should use noise cancelation and the semantic_vad VAD

@https://platform.openai.com/docs/guides/realtime-vad
