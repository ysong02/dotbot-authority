import asyncio
import cbor2.decoder
import uvicorn
import lakers
import websockets
import json
import time
from fastapi import WebSocket
import cbor2
import secrets

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

from attestation_provision import public_key_bytes, basedir, accepted_type_evidence, approved_hash_evidence
from errors import NoMatchError

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
        self.nonces = {}
        #self.nonce = 'a29f62a4c6cdaae5'
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

    async def handle_attestation_proposal (self, cid, proposal_bytes):
        decoded_proposal = cbor2.loads(proposal_bytes)
        print(decoded_proposal)
        selected_type = next((num for num in decoded_proposal if num in accepted_type_evidence), None)
        if selected_type is not None:
            self.nonces[cid] = secrets.token_bytes(8)
            ead_2 = (selected_type, self.nonces[cid])
            return cbor2.dumps(ead_2)
        else:
            raise NoMatchError("No match found in the proposal evidence type list")

    async def evaluate_evidence(self, cid, cbor_bytes, public_key_bytes):
        attestation_result = False
        LOGGER.debug(f"start to evaluate the evidence")
        decoded_info = decode_cose_sign1_message(cbor_bytes, public_key_bytes)
        attester_nonce = decoded_info["nonce"]
        attester_ueid = decoded_info["ueid"]
        attester_hash = decoded_info["measurements"][0]["files_info"][0]["hash_value"]
        attester_software_name = decoded_info["measurements"][0]["software_name"]
        #fs_size = decoded_info["measurements"][0]["files_info"][0]["size"]
        file_name = decoded_info["measurements"][0]["files_info"][0]["fs_name"] 
        #verifier_hash_file = os.path.join(self.file_directory, file_name)

        LOGGER.debug(f"finished parsing evidence, start to compare")

        try:
            nonce = self.nonces[cid]
        except: 
            print("Nonce not found")
        # check nonce
        if nonce.hex() == attester_nonce:
            attestation_result = True
            print("Nonce check: SUCCESS\n Nonce is: ", nonce.hex())
        else:
            print("Nonce check: FAIL\n Nonce from the Attester is: \n", attester_nonce , "\n Nonce from the Verifier is: \n",  nonce.hex())

        # check hash  
        # with open(verifier_hash_file, 'r+b') as file:
        #     data = file.read()
        #     length = len(data)

        #     if length < fs_size:
        #         padding_size = fs_size - length
        #         data += bytes([0xFF] * padding_size)

        # sha256 = hashlib.sha256()
        # sha256.update (data)
        # verifier_hash = sha256.hexdigest()

        # if (verifier_hash.lower() == attester_hash.lower() and attestation_result == True):
        #     print(f"Hash value check: SUCCESS\n Hash value is: {verifier_hash}")
        #     attestation_result = True
        # else:
        #     print(
        #         "Hash value check: FAIL\n "
        #         "Hash result from the Attester is: \n "
        #         f"{attester_hash} \n "
        #         "Hash result from the Verifier is: \n "
        #         f"{verifier_hash}"
        #     )

        if (attester_hash.lower(), attester_software_name) in [(hash.lower(), software_name) for hash, software_name in approved_hash_evidence]:
            attestation_result = True
            print(f"Hash value check: SUCCESS\n Hash value is: {attester_hash}")
        

        notif = DotBotNotificationModel(
            cmd=DotBotNotificationCommand.ATTESTATION_RESULT,
            data=AttestationResult(
                id= attester_ueid,
                attestation_result= attestation_result,
                software_name = decoded_info["measurements"][0]["software_name"],
                fs_name = file_name,
                tag_version = decoded_info["measurements"][0]["tag_version"],
            ),
        )
        self.logger.debug("notify client of attestation result", attestation_result = attestation_result)
        await self.notify_clients(notif)
        return attestation_result