from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware

from routes import router
from wasm import router as wasm_router


class RangeSafeGZipMiddleware(GZipMiddleware):
    async def __call__(self, scope, receive, send):
        # SQLite ranges and HEAD describe offsets in the uncompressed database.
        database_range = (
            scope["type"] == "http"
            and scope["path"] == "/api/database"
            and (scope["method"] == "HEAD" or any(
                name == b"range" for name, _ in scope["headers"]
            ))
        )
        if database_range:
            await self.app(scope, receive, send)
        else:
            await super().__call__(scope, receive, send)


app = FastAPI()
app.add_middleware(RangeSafeGZipMiddleware, compresslevel=6)
app.include_router(router)
app.include_router(wasm_router)
