from typing import Optional


class WSCallEvent:
    def __init__(self, call_cid: Optional[str] = None):
        self.call_cid = call_cid
