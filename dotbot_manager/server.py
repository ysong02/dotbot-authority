"""Module for the web server application."""
from binascii import hexlify

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from dotbot_manager.models import DotBotManagerIdentity

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


@api.get(
    path="/manager/id",
    response_model=DotBotManagerIdentity,
    summary="Return the manager id",
    tags=["manager"],
)
async def controller_id():
    """Returns the id."""
    return DotBotManagerIdentity(
        id="123"
    )
