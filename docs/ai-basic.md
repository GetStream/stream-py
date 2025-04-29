# Introduction

The Python SDK can be used to interact with all Stream products (chat, video, moderation and feeds). The code is generated using the ./generate.sh command so its important to not manually edit files that are code generated.
Code generation takes care of the CRUD layer and organizes the methods in three different places: common, video and chat. This way, you first initialize the SDK (see README.md) with crendetials and then you can
access .video or .chat to use product-specific endpoints.

On both video and chat, many endpoints are related to channel and call resources. To make the code nicer, there is a `Call` resource that can be used to access all methods related to one instance.

Here's an example:

```python
import uuid
from getstream.models import (
    CallRequest,
)

# initialize the sdk using api key and secret
client = Stream(api_key="your_api_key", api_secret="your_api_secret")

# use client.video for video endpoints and .call to create a resource object for a specific call
call = client.video.call("default", uuid.uuid4())

# performs a get_or_create API call
call.get_or_create(
    data=CallRequest(
        created_by_id="tommaso-id",
    ),
)
```

When using the client code, make sure to look at the function signatures and the types definition for the python code. When calling methods such as get_or_create sometimes you need to pass request objects. All request objects are inside the getstream.models module.

All methods using the API like get_or_create return a response type like GetOrCreateResponse, these types also live inside the getstream.models module.

# Projet setup

This project relies on 2 codebases: the Python SDK and the Golang video-sfu code base.

## Python project setup

All lib code lives inside the getstream path of the stream-py repository and tests are under `tests/` The project uses uv to manage dependeincies and pytest for tests

The python project uses uv, venv and pyproject.toml to manage packages. You should never use pip.

## Go project

The go project contains our video SFU as well as a video SDK that we use internally and that we are going to use here in this project. This code lives under the video-sfu path at the same level as the getstream/ python library.

# Python RTC client

The Python client can be used to connect to webRTC calls. To do that we are not going to use a Python webrtc library. Instead, we are going to use our Golang videosdk and use cffi + protobuf to join/leave calls and to communicate data between the two codebases.

The golang sdk code lives in the videosdk/. This is how the code is organized:

videosdk/bindings/ all code related to cgo lives here
videosdk/bindings/main.go this contains the cgo definitions as well as the exported functions to C
videosdk/bindings/events.proto this file contains the model definition used by Go to send data to Python, the mechanism is simple: Python hooks up a callback function and Go uses that callback to forward data

On the python side:

getstream/video/rtc/rtc.py is the file where we have the cffi definitions and the top level functions as well as the top-level python code to join calls
getstream/video/rtc/pb is where we store the protobuf generated code, this code is code generated (see section on how to get this code regenerated)

## Iterating over call events

To receive events from a call, you can use the async context manager pattern with the `join` method. This provides a connection object that acts as an async iterator, yielding events as they're received:

```python
import uuid
from getstream.models import (
    CallRequest,
)

# initialize the sdk using api key and secret
client = Stream(api_key="your_api_key", api_secret="your_api_secret")

# use client.video for video endpoints and .call to create a resource object for a specific call
call = client.video.call("default", uuid.uuid4())

# performs a get_or_create API call
call.get_or_create(
    data=CallRequest(
        created_by_id="tommaso-id",
    ),
)

# Create a call object
rtc_call = client.video.rtc_call("default", uuid.uuid4())

# Method 1: Using event handlers (recommended for most use cases)
async with rtc_call.join("user-id", timeout=10.0) as connection:
    # Register event handlers
    async def handle_audio_packet(event):
        audio = event.rtc_packet.audio
        # Process audio packet
        print(f"Received audio packet: {len(audio.pcm.payload)} bytes")

    async def handle_participant_joined(event):
        participant = event.participant_joined
        print(f"Participant joined: {participant.user_id}")

    async def handle_participant_left(event):
        participant = event.participant_left
        print(f"Participant left: {participant.user_id}")

    # Register the handlers
    await on_event(connection, "audio_packet", handle_audio_packet)
    await on_event(connection, "participant_joined", handle_participant_joined)
    await on_event(connection, "participant_left", handle_participant_left)

    # Process events (handlers will be called automatically)
    async for event in connection:
        # Any additional processing can be done here
        pass

# Method 2: Using match pattern with one-of fields (Python 3.10+)
async with rtc_call.join("user-id", timeout=10.0) as connection:
    async for event in connection:
        match event:
            case events.Event(rtc_packet=rtc_packet) if rtc_packet.audio:
                # Process audio packet
                print(f"Received audio packet: {len(rtc_packet.audio.pcm.payload)} bytes")
            case events.Event(rtc_packet=rtc_packet) if rtc_packet.video:
                # Process video packet
                print(f"Received video packet")
            case events.Event(participant_joined=participant):
                print(f"Participant joined: {participant.user_id}")
            case events.Event(participant_left=participant):
                print(f"Participant left: {participant.user_id}")
            case events.Event(error=error):
                print(f"Error received: {error.code} - {error.message}")
            case _:
                print(f"Unhandled event type: {event}")
```

## Memory management

Because both Python and Go have their own garbage collection, we need to make sure that memory allocated by Go and passed to Python does not get collected by Go's garbage collector (segfaults) and that Python garbage collector will eventually collect the objects (memory leaks).

The current approach is for Go to pass pointers to bytes to Python and mark that memory as untracked; Python will receive that data, copy that into a Python object and then use C.free to release the memory received from Go.

## Code generation

Every change on the Go or Python side that changes C-exported functions or the protobuf events require generating a new .so file and pb files for both go and python. There is a code generation target in getstream/video/rtc/Makefile called all. make all will do all the regeneration and will also copy the new files in place. Make sure to run `make all` every time a change requires new generated code.

The python library relies on the libstreamvideo.so shared object to be present, this file needs to be generated each time the go code that is C exported changes. The make all target does this and takes care of copying the files as well.

DO NOT RUN protoc DIRECTLY OR CHANGE GENEATED CODE! ALWAYS RUN `make all`!!!

## Python Protobuf

The protobuf generated code uses betterproto and not the official protobuf compiler. When writing python code that uses one the protobuf types, make sure to consider that the generated code uses betterproto.

### One-of Support

Protobuf supports grouping fields in a oneof clause. Only one of the fields in the group may be set at a given time. For example, given the proto:

syntax = "proto3";

message Test {
  oneof foo {
    bool on = 1;
    int32 count = 2;
    string name = 3;
  }
}

On Python 3.10 and later, you can use a match statement to access the provided one-of field, which supports type-checking:

test = Test()
match test:
    case Test(on=value):
        print(value)  # value: bool
    case Test(count=value):
        print(value)  # value: int
    case Test(name=value):
        print(value)  # value: str
    case _:
        print("No value provided")
You can also use betterproto.which_one_of(message, group_name) to determine which of the fields was set. It returns a tuple of the field name and value, or a blank string and None if unset.

>>> test = Test()
>>> betterproto.which_one_of(test, "foo")
["", None]

>>> test.on = True
>>> betterproto.which_one_of(test, "foo")
["on", True]

# Setting one member of the group resets the others.
>>> test.count = 57
>>> betterproto.which_one_of(test, "foo")
["count", 57]

# Default (zero) values also work.
>>> test.name = ""
>>> betterproto.which_one_of(test, "foo")
["name", ""]
