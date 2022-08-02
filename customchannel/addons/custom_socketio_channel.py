import logging
import uuid
from typing import Any, Awaitable, Callable, Dict, Optional, Text

import rasa.core.channels.channel
from rasa.core.channels.channel import InputChannel, OutputChannel, UserMessage
import rasa.shared.utils.io
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from socketio import AsyncServer
from rasa.core.channels.socketio import SocketIOOutput, SocketBlueprint

logger = logging.getLogger(__name__)


class CustomSocketIOInput(InputChannel):
    """A socket.io input channel."""

    @classmethod
    def name(cls) -> Text:
        return "custom_sio_channel"

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> InputChannel:
        credentials = credentials or {}
        return cls(
            credentials.get("user_message_evt", "user_uttered"),
            credentials.get("bot_message_evt", "bot_uttered"),
            credentials.get("namespace"),
            credentials.get("session_persistence", False),
            credentials.get("socketio_path", "/socket.io"),
            credentials.get("jwt_key"),
            credentials.get("jwt_method", "HS256"),
        )

    def __init__(
        self,
        user_message_evt: Text = "user_uttered",
        bot_message_evt: Text = "bot_uttered",
        namespace: Optional[Text] = None,
        session_persistence: bool = False,
        socketio_path: Optional[Text] = "/socket.io",
        jwt_key: Optional[Text] = None,
        jwt_method: Optional[Text] = "HS256",
    ):
        """Creates a ``SocketIOInput`` object."""
        self.bot_message_evt = bot_message_evt
        self.session_persistence = session_persistence
        self.user_message_evt = user_message_evt
        self.namespace = namespace
        self.socketio_path = socketio_path
        self.sio: Optional[AsyncServer] = None

        self.jwt_key = jwt_key
        self.jwt_algorithm = jwt_method

    def get_output_channel(self) -> Optional["OutputChannel"]:
        """Creates socket.io output channel object."""
        if self.sio is None:
            rasa.shared.utils.io.raise_warning(
                "SocketIO output channel cannot be recreated. "
                "This is expected behavior when using multiple Sanic "
                "workers or multiple Rasa Open Source instances. "
                "Please use a different channel for external events in these "
                "scenarios."
            )
            return None
        return SocketIOOutput(self.sio, self.bot_message_evt)

    def blueprint(
        self, on_new_message: Callable[[UserMessage], Awaitable[Any]]
    ) -> Blueprint:
        """Defines a Sanic blueprint."""
        # Workaround so that socketio works with requests from other origins.
        # https://github.com/miguelgrinberg/python-socketio/issues/205#issuecomment-493769183
        sio = AsyncServer(async_mode="sanic", cors_allowed_origins=[])
        socketio_webhook = SocketBlueprint(
            sio, self.socketio_path, "socketio_webhook", __name__
        )

        # make sio object static to use in get_output_channel
        self.sio = sio

        @socketio_webhook.route("/", methods=["GET"])
        async def health(_: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @sio.on("connect", namespace=self.namespace)
        async def connect(sid: Text, environ: Dict, auth: Optional[Dict]) -> bool:
            if self.jwt_key:
                jwt_payload = None
                if auth and auth.get("token"):
                    jwt_payload = rasa.core.channels.channel.decode_bearer_token(
                        auth.get("token"), self.jwt_key, self.jwt_algorithm
                    )

                if jwt_payload:
                    logger.debug(f"=> User {sid} connected to socketIO endpoint.")
                    return True
                else:
                    return False
            else:
                logger.debug(f"==> User {sid} connected to socketIO endpoint.")
                return True

        @sio.on("disconnect", namespace=self.namespace)
        async def disconnect(sid: Text) -> None:
            logger.debug(f"User {sid} disconnected from socketIO endpoint.")

        @sio.on("session_request", namespace=self.namespace)
        async def session_request(sid: Text, data: Optional[Dict]) -> None:
            if data is None:
                data = {}
            if "session_id" not in data or data["session_id"] is None:
                data["session_id"] = uuid.uuid4().hex
            if self.session_persistence:
                sio.enter_room(sid, data["session_id"])
            await sio.emit("session_confirm", data["session_id"], room=sid)
            logger.debug(f"===> User {sid} connected to socketIO endpoint.")

        @sio.on(self.user_message_evt, namespace=self.namespace)
        async def handle_message(sid: Text, data: Dict) -> None:
            
            output_channel = SocketIOOutput(sio, self.bot_message_evt)

            if self.session_persistence:
                if not data.get("session_id"):
                    rasa.shared.utils.io.raise_warning(
                        "A message without a valid session_id "
                        "was received. This message will be "
                        "ignored. Make sure to set a proper "
                        "session id using the "
                        "`session_request` socketIO event."
                    )
                    return
                sender_id = data["session_id"]
            else:
                sender_id = sid

            # extracting the customData from the data and setting it into the metadata section so that this will be available in message
            message = UserMessage(
                data["message"], output_channel, sender_id,  metadata=data['customData'], input_channel=self.name()
            )
            
            logger.debug(f"=== ===> message {message.metadata}")
            await on_new_message(message)

        return socketio_webhook
