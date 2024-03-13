"""Module for the web server application."""
import os
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

from dotbot_manager.models import DotBotManagerIdentity
from dotbot_manager.logger import LOGGER

STATIC_FILES_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

api = FastAPI(
    debug=0,
    title="DotBot manager API",
    description="This is the DotBot manager API",
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
    "/manager", StaticFiles(directory=STATIC_FILES_DIR, html=True), name="manager"
)

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
    id_u = api.manager.enrollment_server.decode_voucher_request(voucher_request)
    LOGGER.debug(f"Learned dotbot's identity", id_u=id_u[-1], id_u_hex=hex(id_u[-1]))
    if await api.manager.authorize_dotbot(id_u[-1]):
        voucher_response = api.manager.enrollment_server.prepare_voucher(
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
    basedir = "/home/gfedrech/.dotbots-deployment1"
    id_cred_i = await request.body()
    kid = int(id_cred_i[-1])
    LOGGER.debug(f"Handling credential request", kid=kid)
    try:
        with open(f"{basedir}/dotbot{kid}-cred-rpk.cbor", "rb") as f:
            cred_rpk_ccs = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Credential not found")
    LOGGER.debug(f"Returning credential", kid=kid, cred_rpk_ccs=cred_rpk_ccs.hex(' ').upper())
    return Response(content=cred_rpk_ccs, media_type="binary/octet-stream")


# endpoints for the frontend


@api.get(
    path="/api/v1/id",
    response_model=DotBotManagerIdentity,
    summary="Return the manager id",
    tags=["manager"],
)
async def controller_id():
    """Returns the id. (this is just to test the API)"""
    return DotBotManagerIdentity(id="456")


@api.get(
    path="/api/v1/acl",
    response_model=DotBotManagerIdentity,
    summary="Return the ACL",
)
async def get_acl():
    """Returns the id. (this is just to test the API)"""
    return JSONResponse(content=api.manager.acl)


@api.websocket("/ws/joined-dotbots-log")
async def websocket_endpoint(websocket: WebSocket):
    """Websocket server endpoint."""
    await websocket.accept()
    api.manager.websockets.append(websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in api.manager.websockets:
            api.manager.websockets.remove(websocket)
