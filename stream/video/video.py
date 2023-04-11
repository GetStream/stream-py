from stream.video.call import Call


class Video:
    def __init__(self, stream):
        self.stream = stream

    def call(self, endpoint, request_id, data):
        return Call(self.stream, endpoint, request_id, data)