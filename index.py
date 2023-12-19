from fastapi import FastAPI, Request, WebSocket
from typing import Set
import websocket
from fastapi.responses import JSONResponse
import json
from threading import Thread

app = FastAPI()


websockets: Set[WebSocket] = set()

last_bet_data = {}
gamdom_user = "take123"

def on_message(ws, message):
    global last_bet_data
    last_bet_data = check_user_and_return(message)
    for ws_instance in websockets:
        ws_instance.send_json(last_bet_data)

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    ws_thread = Thread(target=ws.run_forever)
    ws_thread.start()
    print("WebSocket closed")

def on_open(ws):
    print("WebSocket connected")
    ws.send("40/general,", opcode=websocket.ABNF.OPCODE_TEXT)

def check_user_and_return(message):
    start_index = message.find("[")
    end_index = message.rfind("]")
    json_section = message[start_index:end_index + 1]

    try:
        json_data = json.loads(json_section)
        if isinstance(json_data, list) and len(json_data) >= 2 and json_data[0] == "general_stats":
            live_bets = json_data[1].get("liveBets", {})
            recents = live_bets.get("recents", [])

            for recent in recents:
                user_data = recent.get("user", {})
                username = user_data.get("username", "")

                if username == gamdom_user:
                    return recent
                

    except json.JSONDecodeError as e:
        print(f"can't resolve json : {e}")
        
async def connect_to_websocket():
    async with websockets.connect('wss://gamdom.com/socket.io/?EIO=3&transport=websocket') as websocket:  # Remplacez par votre URL WebSocket
        # Envoyer une demande ou un message au serveur WebSocket pour récupérer les données
        await websocket.send("40/general,")
        
        # Attendre la réponse du serveur WebSocket
        response = await websocket.recv()
        return response        
        
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Ajouter la nouvelle connexion WebSocket à l'ensemble
    websockets.add(websocket)

    while True:
        try:
            message = await websocket.receive_text()
            print(f"Received message: {message}")
        except Exception as e:
            print(f"Error: {e}")
            break

    # Supprimer la connexion WebSocket lorsqu'elle est fermée
    websockets.remove(websocket)

    @app.route('/last_bet')
    async def get_last_bet(request: Request):  # Modifier ici pour accepter une requête
        data_from_websocket = await connect_to_websocket()
        
        # Traiter les données reçues si nécessaire
        
        # Retourner les données récupérées en réponse à la requête HTTP
        return JSONResponse(content={"data": data_from_websocket})

if __name__ == "__main__":
    websocket.enableTrace(False)

    ws = websocket.WebSocketApp('wss://gamdom.com/socket.io/?EIO=3&transport=websocket',
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)


    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
