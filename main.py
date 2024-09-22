from fastapi import FastAPI, HTTPException, Response, Cookie, WebSocket
from pydantic import BaseModel
from typing import Optional
from starlette.middleware.cors import CORSMiddleware

# Baseline : https://ummai.cosh.kr/api
app = FastAPI()

from routers import users
from routers.common import *
app.include_router(users.router)

from routers import board
app.include_router(board.router)

from routers import chat
app.include_router(chat.router)

origins = [
    "http://localhost:3000",
    "http://localhost",
    "https://localhost:3000",
    "https://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/session")
def session(session_id: Optional[str] = Cookie(None)):
    if is_session_valid(session_id):
        return {"result" : "valid"}
    return {"result" : "invalid"}
