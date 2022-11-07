
from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect  # HTTPException, status
# from fastapi.security import SecurityScopes
from fastapi.testclient import TestClient
from random import choice, randint
import asyncio
import json
from pydantic import BaseModel
from httpx import AsyncClient
import pytest


app = FastAPI()

CHANNELS = ["A", "B", "C"]


@app.websocket("/sample")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        await websocket.send_json({
            "channel": choice(CHANNELS),
            "data": randint(1, 10)
            }
        )
        await asyncio.sleep(0.5)


ws_clients = []


def get_ws_clients():
    return ws_clients


class Message(BaseModel):
    id: int
    message: str


@app.get("/update")
async def notify(clients=Depends(get_ws_clients)):
    """
    Notify all websocket clients
    """
    await asyncio.wait([ws.send_text("notification!") for ws in clients])
    return {}


@app.get("/")
async def read_main(msg: Message = {"msg": "Hello World"}) -> Message:
    return msg


@app.post("/message")
async def send_msg(msg: Message, clients=Depends(get_ws_clients)):
    """
    Message to all websocket clients
    """
    for ws in clients:
        await ws.send_json(msg.__dict__)
    return msg


@app.websocket_route("/ws")
async def websocket_endpoint2(websocket: WebSocket):
    await websocket.accept()
    ws_clients.append(websocket)
    try:
        while True:
            _ = await websocket.receive_json()
    except WebSocketDisconnect:
        pass
    finally:
        ws_clients.remove(websocket)


def test_main():
    status_code = 200
    test_app = TestClient(app=app)
    response = test_app.get("/")
    assert response.status_code == status_code
    assert response.json() == {"msg": "Hello World"}


def test_message():
    payload = {"id": 1, "message": "Hello"}
    auth = {}
    status_code = 200
    test_app = TestClient(app=app)
    response = test_app.post("/message", data=json.dumps(payload), headers=auth)
    assert response.status_code == status_code
    assert response.json() == payload


@pytest.mark.asyncio
async def test_websocket_endpoint2():
    payload = {"id": 1, "message": "Hello"}
    auth = {}
    ws_auth = {}
    status_code = 200
    ws_connected = True
    test_app = TestClient(app=app)

    with test_app.websocket_connect("/ws", headers=ws_auth) as ws:
        assert bool(get_ws_clients()) == ws_connected
        # response = test_app.post("/message", data=json.dumps(payload), headers=auth)
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/message", data=json.dumps(payload), headers=auth)

        assert response.status_code == status_code
        assert response.json() == payload

        if ws_connected and response.status_code // 100 == 2:
            data = ws.receive_json()
            assert data == payload
