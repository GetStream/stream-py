Anytime you need to change the events in protobuf or change the Go functions exported to C, you must do two things:

- run `make all` from the rtc/ folder on the python repo
- if necessary, adjust the cffi definition in the rtc.py file to match with the new functions

Do not use protoc directly or other make targets for this. make all does everything you need to ensure that both go and python have the generated code and the shared object library in the right place

Any change ot the go code needs a cogegen run with `make all` before Python can use it with the so object

Errors such as

- AttributeError: function/symbol 'EnableMock' not found in library '/Users/tommaso/src/stream-py/getstream/video/rtc/libstreamvideo.so': dlsym(0x396ae69c0, EnableMock): symbol not found
- libstreamvideo.so not found

Indicate that the make all command was not run after changing go/proto files.
