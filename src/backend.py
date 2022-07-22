import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from manager import ConnectionManager
from database import GameDatabase
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
        "method": "update",
        "unique_id": "rfah3430243iog34gsdaf",
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
            response = {"game": "stuff"}

            # Return response to the client
            await websocket.send_json(response)

        except WebSocketDisconnect:
            logging.info(f"* WebSocket from {client_ip} dropped *")
            manager.disconnect(websocket)
            break

        except Exception as e:
            logging.info("error", e)
            break
        
    logging.info(f"Websocket closed => {client_ip}")
