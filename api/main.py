from contextlib import asynccontextmanager

from fastapi import FastAPI

from mcp_server import mcp
from routes import router


@asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)
app.mount('/mcp', mcp.streamable_http_app(
    streamable_http_path='/', stateless_http=True, json_response=True))
