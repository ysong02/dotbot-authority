import asyncio
import uvicorn
import lakers
import websockets
import json
import time
from fastapi import WebSocket

from dotbot_authority.server import api
from dotbot_authority.logger import LOGGER
from dotbot_authority.lake_authz import W, CRED_V
from dotbot_authority.models import (
    DotBotNotificationModel,
    DotBotNotificationCommand,
    AuthorizationResult,
)


class Authority:
    """Main class of the DotBot Authority."""

    def __init__(self):
        self.api = api
        api.authority = self
        self.enrollment_server = lakers.AuthzServerUserAcl(
            W,
            CRED_V,
        )
        self.acl = [1, 43]
        self.authorization_log = []
        self.websockets = []
        self.logger = LOGGER.bind(context=__name__)
        self.logger.debug("Creating Authority instance")

    async def authorize_dotbot(self, id_u):
        """
        Two options:
        - compare with a local acl, notify UI, and return the result
        - ask for the user to decide on the UI, and return the result
        """
        self.logger.debug("Authorizing dotbot", id_u=id_u)
        authorized = id_u in self.acl
        notif = DotBotNotificationModel(
            cmd=DotBotNotificationCommand.AUTHORIZATION_RESULT,
            data=AuthorizationResult(
                timestamp=int(round(time.time() * 1000)), id=id_u, authorized=authorized
            ),
        )
        self.logger.debug("Notifying clients", authorized=authorized)
        await self.notify_clients(notif)
        return authorized

    async def _ws_send_safe(self, websocket: WebSocket, msg: str):
        """Safely send a message to a websocket client."""
        try:
            await websocket.send_text(msg)
        except websockets.exceptions.ConnectionClosedError:
            await asyncio.sleep(0.1)

    async def notify_clients(self, notification):
        """Send a message to all clients connected."""
        self.logger.debug("notify", cmd=notification.cmd.name)
        await asyncio.gather(
            *[
                self._ws_send_safe(
                    websocket, json.dumps(notification.dict(exclude_none=True))
                )
                for websocket in self.websockets
            ]
        )

    async def web(self):
        """Starts the web server application."""
        logger = LOGGER.bind(context=__name__)
        config = uvicorn.Config(api, port=18000, log_level="info", reload=True)
        server = uvicorn.Server(config)

        try:
            logger.info("Starting web server")
            await server.serve()
        except asyncio.exceptions.CancelledError:
            logger.info("Web server cancelled")
        else:
            logger.info("Stopping web server")
            raise SystemExit()

    async def run(self):
        """Launch the authority."""
        tasks = []
        try:
            tasks = [
                asyncio.create_task(self.web()),
            ]
            await asyncio.gather(*tasks)
        except SystemExit:
            self.logger.info("Stopping authority")
        finally:
            for task in tasks:
                task.cancel()
