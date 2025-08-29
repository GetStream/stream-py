import asyncio
import requests
import os
import logging
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel
from aiortc.contrib.media import MediaPlayer
import json

class GPTRealtime:
    """
    A class to manage real-time interactions with the OpenAI API using WebRTC.
    """

    def __init__(self):
        """
        Initializes the GPTRealtime with API key, peer connection, and data channel.
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.pc = RTCPeerConnection()
        self.dc = None
        self.session_config = {
            "session": {
                "type": "realtime",
                "model": "gpt-realtime",
                "audio": {
                    "output": {
                        "voice": "marin"
                    }
                }
            }
        }
        self.session_created_event = asyncio.Event()
        self.audio_track = None
        # Initialize peer connection
        self.initialize_pc()

    def initialize_pc(self):
        """
        Initializes the media players for video and audio.
        """
        # self.video_player = MediaPlayer(
        #     "default:none",
        #     format="avfoundation",
        #     options={"framerate": "30", "video_size": "1280x720"}
        # )
        # self.audio_player = MediaPlayer(
        #     ":3",
        #     format="avfoundation",
        # )
        # # self.pc.addTrack(self.video_player.video)
        # self.pc.addTrack(self.audio_player.audio)
        @self.pc.on("track")
        def on_track(track):
            if track.kind == "video":
                logging.info("Video track received")
            elif track.kind == "audio":
                logging.info("Audio track received")
                self.audio_track = track


    def get_openai_token(self):
        """
        Retrieves a session token from the OpenAI API.

        :return: The session token if successful, None otherwise.
        """
        try:
            url = "https://api.openai.com/v1/realtime/client_secrets"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(url, headers=headers, json=self.session_config)
            response.raise_for_status()
            logging.info("Token retrieval successful")
            return response.json()['value']
        except requests.exceptions.RequestException as e:
            logging.error(f"Token retrieval failed: {e}")
            return None

    def exchange_sdp(self, sdp):
        """
        Exchanges the given SDP with the OpenAI API and returns the response.

        :param sdp: The SDP to exchange.
        :return: The response from the OpenAI API.
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/sdp",
            }

            response = requests.post(
                "https://api.openai.com/v1/realtime/calls?model=gpt-realtime",
                headers=headers,
                data=sdp,
            )

            response.raise_for_status()
            logging.info("SDP exchange successful")

            # Check if the response contains a valid SDP
            if response.text:
                return response.text
            else:
                logging.error("Received empty SDP response")
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"SDP exchange failed: {e}")
            return None

    async def update_session(self):
        """
        Updates the session by sending a session.update message.
        """
        event = {
            "type": "session.update",
            "session": {
                "type": "realtime",
                "model": "gpt-realtime",
                "output_modalities": ["audio"],
                "audio": {
                    "input": {
                        "turn_detection": {"type": "semantic_vad", "create_response": True}
                    },
                    "output": {
                        "voice": "marin",
                        "speed": 1.0
                    }
                },
            }
        }
        await self.send_client_event(event)

    async def start_session(self, track):
        """
        Starts the WebRTC session by creating a data channel, sending an SDP offer,
        and setting the remote SDP answer.
        """
        try:
            # Get a session token for OpenAI Realtime API
            self.token = self.get_openai_token()
            if track is not None:
                self.pc.addTrack(track)

            # Create a data channel for sending and receiving events
            self.dc = self.pc.createDataChannel("oai-events")

            @self.dc.on("open")
            def on_open():
                logging.info("Data channel is open")

            @self.dc.on("message")
            def on_message(message):
                logging.info(f"Received message: {message}")
                try:
                    message_data = json.loads(message)
                    if message_data.get('type') == 'session.created':
                        logging.info("Session created message received")
                        # Set an event to signal that the session is created
                        self.session_created_event.set()
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to decode message as JSON: {e}")

            # Create an SDP offer and send it to the OpenAI API
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)

            sdp = self.exchange_sdp(offer.sdp)

            # Check if the SDP exchange was successful
            if sdp is None:
                logging.error("Failed to exchange SDP, aborting session start")
                return

            answer = RTCSessionDescription(sdp, "answer")
            await self.pc.setRemoteDescription(answer)

            logging.info("SDP exchange completed, waiting for session.created message")

            # Wait for the session.created message
            await self.session_created_event.wait()

            # Update the session
            await self.update_session()

            logging.info("Session started successfully")
        except Exception as e:
            logging.error(f"Failed to start session: {e}")

    async def stop_session(self):
        """
        Stops the WebRTC session by closing the data channel and peer connection.
        """
        try:
            # Close the data channel
            if self.dc:
                self.dc.close()
                self.dc = None  # Set data channel to None after closing

            # Stop all tracks on the peer connection
            for sender in self.pc.getSenders():
                if sender.track:
                    sender.track.stop()

            # Close the peer connection
            await self.pc.close()

            logging.info("Session stopped successfully")
        except Exception as e:
            logging.error(f"Failed to stop session: {e}")

    async def send_client_event(self, message):
        """
        Sends a message through the data channel.

        :param message: The message to send.
        """
        try:
            if self.dc:
                # Serialize the message to a JSON string
                message_json = json.dumps(message)
                # Send the message through the data channel
                self.dc.send(message_json)
                logging.info(f"Sent message: {message_json}")
        except Exception as e:
            logging.error(f"Failed to send message: {e}")

    async def send_text_message(self, text):
        """
        Constructs a message event and sends it using send_client_event.

        :param text: The text message to send.
        """
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}]
            }
        }
        await self.send_client_event(event)
        await self.send_client_event({"type": "response.create"})

# Example usage
if __name__ == "__main__":
    gpt_realtime = GPTRealtime()
    asyncio.run(gpt_realtime.start_session())
    # Example of sending a text message
    asyncio.run(gpt_realtime.send_text_message("Hello, OpenAI!"))
    # Stop the session
    asyncio.run(gpt_realtime.stop_session())
