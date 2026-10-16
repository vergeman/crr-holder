from fastapi import FastAPI

from routes import router
from wasm import router as wasm_router


app = FastAPI()
app.include_router(router)
app.include_router(wasm_router)
