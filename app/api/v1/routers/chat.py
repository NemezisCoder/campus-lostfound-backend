from fastapi import APIRouter, WebSocket

router = APIRouter(prefix="/chat")

@router.websocket("/ws")
async def chat_ws(ws: WebSocket):
    await ws.accept()
    await ws.send_json({"message": "connected"})
    await ws.close()
