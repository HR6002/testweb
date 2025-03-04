from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import json
import uvicorn

app = FastAPI()
connections = {}

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

        <script>
            let socket;
            function connectWebSocket() {
                let username = document.getElementById("username").value;
                socket = new WebSocket(`ws://${window.location.host}/ws/${username}`);
                socket.onopen = () => {
                    document.getElementById("response").innerText = `Connected as ${username}`;
                };
                socket.onmessage = (event) => {
                    displayMessage(event.data);
                };
                socket.onclose = () => {
                    document.getElementById("response").innerText = "Disconnected";
                };
            }
            function sendMessage() {
                let recipient = document.getElementById("recipient").value;
                let message = document.getElementById("message").value;
                if (socket && socket.readyState === WebSocket.OPEN) {
                    let data = JSON.stringify({recipient, message});
                    socket.send(data);
                    displayMessage(`You: ${message}`);
                }
            }
            function displayMessage(msg) {
                let chat = document.getElementById("chat");
                let messageElement = document.createElement("p");
                messageElement.innerText = msg;
                chat.appendChild(messageElement);
            }
        </script>
    </body>
    </html>
    """

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    connections[username] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            recipient = data.get("recipient")
            message = data.get("message")
            print(f"{username} to {recipient}: {message}")
            
            # Send message to the recipient if they are connected
            if recipient in connections:
                await connections[recipient].send_text(f"{username}: {message}")
            
            # Also send message back to the sender
            await websocket.send_text(f"You: {message}")
    except:
        pass
    finally:
        del connections[username]



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)