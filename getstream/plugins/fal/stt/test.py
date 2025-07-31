from getstream.plugins.fal.stt.stt import FalWizperSTT

stt = FalWizperSTT(task="transcribe")
stt.process_audio(b"Hello, world!")
