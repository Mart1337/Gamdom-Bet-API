from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from threading import Thread
import websocket
import json

app = Flask(__name__)
socketio = SocketIO(app)

last_bet_data = {}
gamdom_user = "banksy 3"

def on_message(ws, message):
    global last_bet_data
    last_bet_data = check_user_and_return(message)
    socketio.emit('last_bet_update', last_bet_data) 
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

    return {} 

@app.route('/last_bet')
def get_last_bet():
    global last_bet_data
    if last_bet_data:
        return jsonify(last_bet_data)
    else:
        return jsonify({"message": f"No bet found for {gamdom_user}"})

@socketio.on('connect')
def handle_connect():
    emit('last_bet_update', last_bet_data)

if __name__ == "__main__":
    websocket.enableTrace(False)

    ws = websocket.WebSocketApp('wss://gamdom.com/socket.io/?EIO=3&transport=websocket',
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open

    ws_thread = Thread(target=ws.run_forever)
    ws_thread.start()

    socketio.run(app)  
