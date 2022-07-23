import logging

from database import GameDatabase
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from manager import ConnectionManager

logging.basicConfig(format="%(asctime)s - %(filename)s - %(message)s", level=logging.INFO)

app = FastAPI(title="Old Fashioned Orcs")
manager = ConnectionManager()
db = GameDatabase()


@app.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """
    This endpoint will handle the session of a player.

    Example JSON payload:
    {
        "unique_id": "",
        "nickname": "coolname",
        "position_x": 150,
        "position_y": 350,
        "level": 1
    }
    :param payload: json object
    """
    await manager.connect(websocket)
    client_ip = websocket.client.host
    logging.info(f"New WebSocket => {client_ip}")

    while True:
        try:
            # Read payload from client
            payload = await manager.update(websocket)

            # TODO => Interact with the game here using the payload & create the appropriate response
            # Currently just doing a pingback of the client payload for testing sake and so that the linter's happy

            # Return response to the client
            await websocket.send_json(payload)

        except WebSocketDisconnect:
            logging.info(f"* WebSocket from {client_ip} dropped *")
            manager.disconnect(websocket)
            break

        except Exception as e:
            logging.info("error", e)
            break

    logging.info(f"Websocket closed => {client_ip}")
