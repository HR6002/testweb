from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import uvicorn
from collections import deque
import time
from fastapi import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")  # Serve static files

connections = {}
message_history = {}  # Dictionary to store user message history for rate limiting

# Rate limiter constants
MAX_MESSAGES_PER_MINUTE = 20
TIME_FRAME = 60  # Time frame in seconds (1 minute)
MAX_MESSAGE_LENGTH = 20  # Max message length (in characters)

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple FastAPI App</title>
    </head>
    <body>
        <input type="text" id="username" placeholder="Enter username">
        <button onclick="connectWebSocket()">Go</button>
        <br>
        <input type="text" id="recipient" placeholder="Enter recipient">
        <input type="text" id="message" placeholder="Enter message">
        <button onclick="sendMessage()">Send</button>
        <p id="response"></p>
        <div id="chat"></div>

        <script src="/static/script.js"></script>  <!-- Link to the external JavaScript file -->
    </body>
    </html>
    """

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    connections[username] = websocket
    
    # Initialize message history for this user if not already present
    if username not in message_history:
        message_history[username] = deque()

    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            recipient = data.get("recipient")
            message = data.get("message")
            current_time = time.time()

            # Check if the message length exceeds the limit
            if len(message) > MAX_MESSAGE_LENGTH:
                await websocket.send_text(f"Message is too long. Maximum allowed length is {MAX_MESSAGE_LENGTH} characters.")
                continue

            # Check if user has exceeded message limit
            message_history[username].append(current_time)

            # Remove old messages beyond the 1-minute time frame
            while message_history[username] and message_history[username][0] < current_time - TIME_FRAME:
                message_history[username].popleft()

            # If user has exceeded the limit, reject the message
            if len(message_history[username]) > MAX_MESSAGES_PER_MINUTE:
                await websocket.send_text("Rate limit exceeded. Please wait before sending more messages.")
                continue

            print(f"{username} to {recipient}: {message}")
            
            # Send message to the recipient if they are connected
            if recipient in connections:
                await connections[recipient].send_text(f"{username}: {message}")
            
            # Also send message back to the sender
            await websocket.send_text(f"You: {message}")
    except WebSocketDisconnect:
        pass
    finally:
        del connections[username]
        del message_history[username]
