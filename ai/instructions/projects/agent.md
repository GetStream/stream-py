create a base Agent class that exposes these methods:

- on_track(participant, track)
- on(event_name, handler)
- on_track_ended(participant, track)
- subscribe_video(participant, track, options)
- unsubscribe_video(participant, track)
- leave()
- join()
- recv(participant, frame: av.Frame)
- send()

- this class exposes an async run() method that blocks until the leave method is called

the constructor of this class should receive these parameter:
- call object (same type as client.video.call)
- user_id for the agent (optional, string uuid v4 if not provided)
