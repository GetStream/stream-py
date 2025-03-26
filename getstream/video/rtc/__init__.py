try:
    import aiortc
except ImportError:
    # before throwing, suggest the user to install the `webrtc` optional dependency
    raise ImportError(
        "The `webrtc` optional dependency is required to use the `getstream.video.rtc` module. "
        "Please install it using the following command: `pip install getstream[webrtc]`"
    )
