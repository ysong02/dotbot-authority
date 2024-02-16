"""Module for the web server application."""
from binascii import hexlify

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from dotbot_manager.models import DotBotManagerIdentity
from dotbot_manager.logger import LOGGER

# STATIC_FILES_DIR = os.path.join(os.path.dirname(__file__), "frontend", "build")


api = FastAPI(
    debug=0,
    title="DotBot controller API",
    description="This is the DotBot controller API",
    # version=pydotbot_version(),
    docs_url="/api",
    redoc_url=None,
)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# api.mount(
#     "/dotbots", StaticFiles(directory=STATIC_FILES_DIR, html=True), name="dotbots"
# )

# endpoints for lake-authz

class RawResponse(Response):
    media_type = "binary/octet-stream"

@api.post(
    path="/.well-known/lake-authz/voucher-request",
    summary="Handles a voucher request",
)
async def lake_authz_voucher_request(request: Request):
    """Handles a Voucher Request."""
    voucher_request = await request.body()
    LOGGER.debug(f"Handling voucher request: {hexlify(voucher_request).decode()}")
    voucher_response = api.manager.enrollment_server.handle_voucher_request(voucher_request)
    LOGGER.debug(f"Voucher response is: {hexlify(voucher_response).decode()}")
    return RawResponse(content=bytes(voucher_response))

# endpoints for the frontend

@api.get(
    path="/manager/id",
    response_model=DotBotManagerIdentity,
    summary="Return the manager id",
    tags=["manager"],
)
async def controller_id():
    """Returns the id. (this is just to test the API)"""
    return DotBotManagerIdentity(
        id="456"
    )

@api.get(
    path="/manager/acl",
    response_model=DotBotManagerIdentity,
    summary="Return the ACL",
)
async def get_acl():
    """Returns the id. (this is just to test the API)"""
    return JSONResponse(content=[1, 2, 3])
