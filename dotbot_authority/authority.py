import asyncio
import uvicorn
import lakers
import websockets
import json
import time
from fastapi import WebSocket

from server import api
from logger import LOGGER
from lake_authz import W, CRED_V
from models import (
    DotBotNotificationModel,
    DotBotNotificationCommand,
    AuthorizationResult,
    AttestationResult
)

import hashlib
from attestation_decoder import decode_cose_sign1_message
from cryptography.exceptions import InvalidSignature
import os

from attestation_provision import nonce, public_key_bytes, basedir

# CHECK_SUCCESS = 1
# CHECK_ERROR_NONCE = -1
# CHECK_ERROR_SIGNATURE = -2
# CHECK_ERROR_HASH_IMAGE = -3
# CHECK_GENERAL_ERROR = -4

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
        self.file_directory = basedir
        self.nonce = 'a29f62a4c6cdaae5'
        self.public_key_bytes = public_key_bytes

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

                
    async def evaluate_evidence(self, cbor_bytes, verifier_nonce, public_key_bytes):
        #status = CHECK_SUCCESS
        attestation_result = False

        decoded_info = decode_cose_sign1_message(cbor_bytes, public_key_bytes)
        attester_nonce = decoded_info["nonce"]
        attester_hash = decoded_info["measurements"][0]["files_info"][0]["hash_value"]
        fs_size = decoded_info["measurements"][0]["files_info"][0]["size"]
        #file_name = decoded_info["measurements"][0]["files_info"][0]["fs_name"] 
        file_name = "01drv_attestation-nrf52840dk.bin"
        verifier_hash_file = os.path.join(self.file_directory, file_name)

        # check nonce
        if verifier_nonce == attester_nonce:
            print("Nonce check: SUCCESS\n Nonce is: ", verifier_nonce)
        else:
            print("Nonce check: FAIL\n Nonce from the Attester is: \n", attester_nonce , "\n Nonce from the Verifier is: \n",  verifier_nonce)
            #status = CHECK_ERROR_NONCE

        # check hash  

        with open(verifier_hash_file, 'r+b') as file:
            data = file.read()
            length = len(data)

            if length < fs_size:
                padding_size = fs_size - length
                data += bytes([0xFF] * padding_size)

        sha256 = hashlib.sha256()
        sha256.update (data)
        verifier_hash = sha256.hexdigest()

        if verifier_hash.lower() == attester_hash.lower():
            print(f"Hash value check: SUCCESS\n Hash value is: {verifier_hash}")
            attestation_result = True
        else:
            print(
                "Hash value check: FAIL\n "
                "Hash result from the Attester is: \n "
                f"{attester_hash} \n "
                "Hash result from the Verifier is: \n "
                f"{verifier_hash}"
            )
            #status = CHECK_ERROR_HASH_IMAGE

        notif = DotBotNotificationModel(
            cmd=DotBotNotificationCommand.ATTESTATION_RESULT,
            data=AttestationResult(
                id=43,
                attestation_result= attestation_result,
                software_name = decoded_info["measurements"][0]["software_name"],
                fs_name = file_name,
                fs_size = fs_size,
                tag_version = decoded_info["measurements"][0]["tag_version"],
            ),
        )
        self.logger.debug("notify client of attestation result", attestation_result = attestation_result)
        await self.notify_clients(notif)
        return attestation_result