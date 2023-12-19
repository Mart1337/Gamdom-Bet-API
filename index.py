import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import websocket
import json

app = FastAPI()



last_bet_data = {}
gamdom_user = "Martizio"




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
    ws = websocket.WebSocket()
    ws.connect('wss://gamdom.com/socket.io/?EIO=3&transport=websocket')
    ws.send("40/general,")
    response = ws.recv()
    ws.close()
    return response

@app.route('/last_bet')
async def get_last_bet(request: Request):
    try:
        data_from_websocket = await connect_to_websocket()
        checked = check_user_and_return(data_from_websocket)
        return JSONResponse(content={"data": checked})
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

if __name__ == "__main__":
  

    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
