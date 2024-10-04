"""Module for the web server application."""
import os
import cbor2
from binascii import hexlify

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Request,
    Response,
)
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models import DotBotAuthorityIdentity
from logger import LOGGER


STATIC_FILES_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

api = FastAPI(
    debug=0,
    title="DotBot Authority API",
    description="This is the DotBot Authority API",
    # version=pydotbot_version(),
    docs_url="/api-docs",
    redoc_url=None,
)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api.mount(
    "/authority", StaticFiles(directory=STATIC_FILES_DIR, html=True), name="authority"
)

# api.mount(
#     "/attesetation", StaticFiles(directory=ATTESTATION_FILES_DIR, html= True), name="attestation"
# )

# endpoints for lake-authz


@api.post(
    path="/.well-known/lake-authz/voucher-request",
    summary="Handles a voucher request",
)
async def lake_authz_voucher_request(request: Request):
    """Handles a Voucher Request."""
    voucher_request = await request.body()
    LOGGER.debug(
        f"Handling voucher request", voucher_request=hexlify(voucher_request).decode()
    )
    id_u = api.authority.enrollment_server.decode_voucher_request(voucher_request)
    LOGGER.debug(f"Learned dotbot's identity", id_u=id_u[-1], id_u_hex=hex(id_u[-1]))
    if await api.authority.authorize_dotbot(id_u[-1]):
        voucher_response = api.authority.enrollment_server.prepare_voucher(
            voucher_request
        )
        LOGGER.debug(
            f"Dotbot authorized, prepared voucher response",
            voucher_response=hexlify(voucher_response).decode(),
        )
        return Response(
            content=bytes(voucher_response), media_type="binary/octet-stream"
        )
    else:
        LOGGER.debug(f"Dotbot not authorized")
        raise HTTPException(status_code=403)

@api.post(
    path="/.well-known/lake-authz/cred-request",
    summary="Handles a credential request",
)
async def lake_authz_credential_request(request: Request):
    """Handles a Credential Request."""
    basedir = "C:\\Users\\yusong\\Downloads\\test-edhoc-handshake\\dotbots-deployment1"
    id_cred_i = await request.body()
    kid = int(id_cred_i[-1])
    LOGGER.debug(f"Handling credential request", kid=kid)
    try:
        with open(f"{basedir}\\dotbot{kid}-cred-rpk.cbor", "rb") as f:
            cred_rpk_ccs = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Credential not found")
    LOGGER.debug(f"Returning credential", kid=kid, cred_rpk_ccs=cred_rpk_ccs.hex(' ').upper())
    return Response(content=cred_rpk_ccs, media_type="binary/octet-stream")

#endpoints for lake-ra


# need to improve the function, select evidence type, change the exception
@api.post(
    path="/.well-known/lake-ra/attestation-proposal",
    summary="Handles an attestation proposal",
)
async def lake_ra_attestation_proposal(request: Request):
    """Handles an attestation proposal."""
    attestation_proposal = await request.body()
    #print(f"Evidence type: {type(evidence)}, Evidence: {evidence.hex()}")
    LOGGER.debug(
        f"Handling attestation proposal", attestation_proposal=hexlify(attestation_proposal).decode()
    )
    if attestation_proposal!=None:
        attestation_request_content = [258]
        attestation_request = cbor2.dumps(attestation_request_content)
        LOGGER.debug(
            f"prepared attestation request",
            attestation_request=hexlify(attestation_request).decode(),
        )
        return Response(
            content=attestation_request, media_type="binary/octet-stream"
        )
    else:
        LOGGER.debug(f"Attestation proposal is none")
        raise HTTPException(status_code=403)

@api.post(
    path="/.well-known/lake-ra/evidence",
    summary="Handles an evidence attestation token",
)
async def lake_ra_evidence(request: Request):
    """Handles an evidence attestation token."""
    evidence = await request.body()
    print(f"Evidence type: {type(evidence)}, Evidence: {evidence.hex()}")
    
    nonce = api.authority.nonce
    public_key_bytes = api.authority.public_key_bytes
    if await api.authority.evaluate_evidence(evidence, nonce, public_key_bytes):
        attestation_result = b"verified"
        return Response(content= cbor2.dumps(attestation_result), media_type="binary/octet-stream")
    else:
        return Response(content= b"attestation test result is fail", media_type="binary/octet-stream")
        #raise HTTPException(status_code=400, detail="Verification failed")

# endpoints for the frontend


@api.get(
    path="/api/v1/id",
    response_model=DotBotAuthorityIdentity,
    summary="Return the authority id",
    tags=["authority"],
)
async def controller_id():
    """Returns the id. (this is just to test the API)"""
    return DotBotAuthorityIdentity(id="456")


@api.get(
    path="/api/v1/acl",
    response_model=DotBotAuthorityIdentity,
    summary="Return the ACL",
)
async def get_acl():
    """Returns the id. (this is just to test the API)"""
    return JSONResponse(content=api.authority.acl)


@api.websocket("/ws/joined-dotbots-log")
async def websocket_endpoint(websocket: WebSocket):
    """Websocket server endpoint."""
    await websocket.accept()
    api.authority.websockets.append(websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in api.authority.websockets:
            api.authority.websockets.remove(websocket)
