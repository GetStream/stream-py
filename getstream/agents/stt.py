import abc
from pyee.asyncio import AsyncIOEventEmitter


class STT(AsyncIOEventEmitter, abc.ABC):

    def __init__(self):
        super().__init__()
        self._track = None

    def add_track(self, track):
        self._track = track
