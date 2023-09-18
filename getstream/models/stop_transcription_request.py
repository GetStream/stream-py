from dataclasses import dataclass

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class StopTranscriptionRequest:
    ...
