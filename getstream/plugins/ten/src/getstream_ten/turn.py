"""TEN Turn Detection wrapper for Stream plugins.
"""
import logging
from typing import Literal

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)

_STATES = [
    "finished",   # user completed thought – respond now
    "unfinished", # user paused – probably will continue
    "wait",       # user asked the bot to stay silent
]


class _Model:
    """Lazy-loaded singleton shared by all instances."""

    tok = None
    mdl = None

    @classmethod
    def ensure(cls):
        if cls.tok is None:
            logger.info("Downloading TEN turn-detection weights (HF)")
            cls.tok = AutoTokenizer.from_pretrained("TEN-framework/TEN_Turn_Detection")
            cls.mdl = AutoModelForSequenceClassification.from_pretrained(
                "TEN-framework/TEN_Turn_Detection"
            )
            cls.mdl.eval()


class TENTurnDetector:
    """Call the instance with a transcript → returns one of the 3 states."""

    def __init__(self, device: str = "cpu"):
        _Model.ensure()
        self.device = torch.device(device)
        _Model.mdl.to(self.device)

    def __call__(self, text: str) -> Literal["finished", "unfinished", "wait"]:
        inputs = _Model.tok(text, return_tensors="pt", truncation=True).to(self.device)
        with torch.no_grad():
            logits = _Model.mdl(**inputs).logits.squeeze()
        label = int(logits.argmax())
        return _STATES[label] 