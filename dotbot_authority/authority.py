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
import attestation_decoder
from cryptography.exceptions import InvalidSignature
import os

from attestation_provision import public_key_bytes, public_key_controller, basedir, accepted_type_evidence, approved_hash_dotbot, freshness_threshold, node_to_key_id, node_public_key_list
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
        #self.acl = [1, 43]
        self.acl = approved_hash_dotbot
        self.authorization_log = []
        self.websockets = []
        self.logger = LOGGER.bind(context=__name__)
        self.logger.debug("Creating Authority instance")
        self.file_directory = basedir
        self.nonces = []
        self.nonce_controller = None
        #self.nonce = 'a29f62a4c6cdaae5'
        self.public_key_bytes = public_key_bytes
        self.public_key_controller = public_key_controller

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

    async def handle_attestation_proposal (self, proposal_bytes):
        decoded_proposal = cbor2.loads(proposal_bytes)
        print(decoded_proposal)
        selected_type = next((num for num in decoded_proposal if num in accepted_type_evidence), None)
        if selected_type is not None:
            nonce= secrets.token_bytes(8)
            self.nonces.append(nonce.hex())
            ead_2 = (selected_type, nonce)
            return cbor2.dumps(ead_2)
        else:
            raise NoMatchError("No match found in the proposal evidence type list")

    async def evaluate_evidence(self, cbor_bytes, public_key_bytes, approved_hash_evidence, model_type: int):
        attestation_result = False
        LOGGER.debug(f"start to evaluate the evidence")
        decoded_info = attestation_decoder.decode_cose_sign1_message(cbor_bytes, public_key_bytes)
        attester_nonce = decoded_info["nonce"]
        attester_ueid = decoded_info["ueid"]
        attester_hash = decoded_info["measurements"][0]["files_info"][0]["hash_value"]
        #attester_software_name = decoded_info["measurements"][0]["software_name"]
        #file_name = decoded_info["measurements"][0]["files_info"][0]["fs_name"] 
        #verifier_hash_file = os.path.join(self.file_directory, file_name)

        LOGGER.debug(f"finished parsing evidence, start to compare")
        # check nonce
        if (model_type == 0):
            # nonce = self.nonces[cid]
            if (attester_nonce in self.nonces):
                print("Nonce check: SUCCESS\n Nonce is: ", attester_nonce)
                self.nonces.remove(attester_nonce)
                attestation_result = True
            else:
                print("Nonce check: DIFFERENT\n Nonce from the Attester is: \n", attester_nonce )

        if (model_type == 1):
        
            if self.nonce_controller.hex() == attester_nonce:
                attestation_result = True
                print("Nonce check: SUCCESS\n Nonce is: ", attester_nonce)
            else:
                print("Nonce check: DIFFERENT\n Nonce from the Attester is: \n", attester_nonce)

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

        # if (attester_hash.lower()) in [(hash.lower()) for hash in approved_hash_evidence]:
        #     attestation_result = True
        #     result_version = "v1.0"
        #     print(f"Firmware Hash value check: SUCCESS\n Hash value is: {attester_hash}")
        # else:
        #     attestation_result = False
        #     print(f"Firmware Hash value check: FAIL\n Hash value is: {attester_hash}")
        #     if (attester_hash.lower()) in [(hash.lower()) for hash in list_hash_versions]:
        #         result_version = "v0.9"
        #     else:
        #         result_version = "not recognized"

        # notif = DotBotNotificationModel(
        #     cmd=DotBotNotificationCommand.ATTESTATION_RESULT,
        #     data=AttestationResult(
        #         timestamp=int(round(time.time() * 1000)),
        #         id= attester_ueid,
        #         decision= attestation_result,
        #         #software_name = decoded_info["measurements"][0]["software_name"],
        #         #fs_name = file_name,
        #         #tag_version = decoded_info["measurements"][0]["tag_version"],
        #         firmware_hash = attester_hash,
        #         attestation_result = result_version,
        #     ),
        # )
        # self.logger.debug("notify client of attestation result", attestation_result = attestation_result)
        # await self.notify_clients(notif)
        return attestation_result
    
    async def mr_swarm_verification_result(self, verification_request, freshness_threshold, ):
        asn_ul, asn_offset, evidence_cbor, node_id = cbor2.loads(verification_request)
        version_attester, key_id_attester, signature_attester = cbor2.loads(evidence_cbor)
        
        # check freshness 
        if (asn_offset > freshness_threshold):
            return attestation_decoder.mr_swarm_generate_verification_response(False)
        
        asn_dl = asn_ul - asn_offset
        if (attestation_decoder.mr_swarm_check_signature(signature_attester, asn_dl, version_attester, node_id)):
            return attestation_decoder.mr_swarm_generate_verification_response(True)
        else:
            return attestation_decoder.mr_swarm_generate_verification_response(False)
