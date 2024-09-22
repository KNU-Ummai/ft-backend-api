from fastapi import APIRouter, HTTPException, Response, Cookie, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import pymysql, time
from uuid import uuid4
from routers.common import *

router = APIRouter(
    tags=["users"]
)

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, id, websocket: WebSocket):
        self.active_connections[id] = websocket

    def disconnect(self, id):
        del self.active_connections[id]

    async def send(self, message: str, id):
        websocket = self.active_connections[id]
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)


manager = ConnectionManager()
global_client_id = 1
@router.websocket("/{target_id}")
async def websocket_endpoint(target_id, websocket: WebSocket):
    await websocket.accept()
    session_id = websocket.cookies.get("session_id")
    if not is_session_valid(session_id):
        await websocket.send_text("invalid_session")
        await websocket.close()
        return
    
    conn, cur = connect_db()
    query = 'SELECT std_no FROM user WHERE id=%s'
    cur.execute(query, target_id)
    row = cur.fetchone()
    
    if not row:
        await websocket.send_text("invalid_target")
        await websocket.close()
        conn.close()
        return

    target_std_no = row[0]
    id = sessData[session_id]["id"]
    std_no = sessData[session_id]["std_no"]
    await manager.connect(id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()

            query = 'INSERT INTO chat VALUES(%s,%s,%s,%s,%s)'
            query_params = tuple([None, std_no, target_std_no, int(time.time()), data])
            cur.execute(query, query_params)
            conn.commit()
            row = cur.fetchone()
            
            await manager.send(id, target_id)
    except WebSocketDisconnect:
        manager.disconnect(id)
        conn.close()