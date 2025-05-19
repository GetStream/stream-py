Anytime you need to change the events in protobuf or change the Go functions exported to C, you must do two things:

- run `make all` inside the python repo inside getstream/video/rtc/
- if necessary, adjust the cffi definition in the getstream/video/rtc.py file to match with the new functions

Do not use protoc directly or other make targets for this. The make all target does everything you need to ensure that both go and python have the generated code and the shared object library in the right place

Any change ot the go code needs a cogegen run with `make all` before Python can use it with the so object

If you change a protobuf type, you also need to call `make all` so that both Python and Go have the new code.

If you need to create a new type, make sure to first create it in protobuf, regenerate the code and only after that use it in Go (otherwise you get a compile error from make all).

Errors such as

- AttributeError: function/symbol 'EnableMock' not found in library '/Users/tommaso/src/stream-py/getstream/video/rtc/libstreamvideo.so': dlsym(0x396ae69c0, EnableMock): symbol not found
- libstreamvideo.so not found

Indicate that the make all command was not run after changing go/proto files.
