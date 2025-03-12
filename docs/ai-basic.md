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
    MemberRequest,
)

call = client.video.call("default", uuid.uuid4())
call.get_or_create(
    data=CallRequest(
        created_by_id="tommaso-id",
        members=[
            MemberRequest(user_id="thierry-id"),
            MemberRequest(user_id="tommaso-id"),
        ],
    ),
)
```


# Projet setup

This project relies on 2 codebases: the Python SDK and the video-sfu code base:

## Python project setup

All lib code lives inside the getstream path of the stream-py repository and tests are under `tests/` The project uses uv to manage dependeincies and pytest for tests

## Go project

The go project contains our video SFU as well as a video SDK that we use internally and that we are going to use here in this project.

# Running python tests

It is important to always write and run test for all new code and changes, tests should use existing conftest fixtures when possible and in general you should not create too much repeated code in tests. When applicable it is best to create fixtures or test helpers and re-use them (see conftest.py file for that).


# RTC client

The Python client can be used to connect to webRTC calls. To do that we are not going to use a Python webrtc library. Instead, we are going to use our Golang videosdk and use cffi + protobuf to join/leave calls and to communicate data between the two codebases.

The golang sdk code lives in the videosdk/ path of the video-sfu repository. This is how the code is organized:

videosdk/bindings/main.go this contains the cgo definitions as well as the exported functions to C
videosdk/bindings/events.proto this file contains the model definition used by Go to send data to Python, the mechanism is simple: Python hooks up a callback function and Go uses that callback to forward data

On the python side:

getstream/video/rtc/rtc.py is the file where we have the cffi definitions and the top level functions.
getstream/video/rtc/pb is where we store the protobuf generated code, this code is code generated (see section on how to get this code regenerated)

## Memory management

Because both Python and Go have their own garbage collection, we need to make sure that memory allocated by Go and passed to Python does not get collected by Go's garbage collector (segfaults) and that Python garbage collector will eventually collect the objects (memory leaks).

The current approach is for Go to pass pointers to bytes to Python and mark that memory as untracked; Python will receive that data, copy that into a Python object and then use C.free to release the memory received from Go.

## Code generation

Every change on the Go or Python side that changes C-exported functions or the protobuf events require generating a new .so file and pb files for both go and python. There is a code generation target in getstream/video/rtc/Makefile called all. make all will do all the regeneration and will also copy the new files in place. Make sure to run `make all` every time a change requires new generated code.

The python library relies on the libstreamvideo.so shared object to be present, this file needs to be generated each time the go code that is C exported changes. The make all target does this and takes care of copying the files as well.

## Python Protobuf

The protobuf generated code uses betterproto and not the official protobuf compiler. When writing python code that uses one the protobuf types, make sure to consider that the generated code uses betterproto.
