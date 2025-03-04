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
                let protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
                socket = new WebSocket(`${protocol}${window.location.host}/ws/${username}`);
                
                socket.onopen = () => {
                    document.getElementById("response").innerText = `Connected as ${username}`;
                    console.log(`WebSocket opened as ${username}`);
                };

                socket.onmessage = (event) => {
                    if (event.data) {
                        displayMessage(event.data);
                    }
                };

                socket.onclose = (event) => {
                    document.getElementById("response").innerText = "Disconnected";
                    console.log("WebSocket closed", event);
                };

                socket.onerror = (event) => {
                    console.error("WebSocket error:", event);
                };
            }

            function sendMessage() {
                let recipient = document.getElementById("recipient").value;
                let message = document.getElementById("message").value;
                if (socket && socket.readyState === WebSocket.OPEN) {
                    let data = JSON.stringify({recipient, message});
                    socket.send(data);
                    console.log(`Sending message: ${data}`);
                    displayMessage(`You: ${message}`);
                } else {
                    console.log("WebSocket not open");
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
            data = await websocket.receive_text()  # Receive message from client
            data = json.loads(data)  # Deserialize incoming JSON
            recipient = data.get("recipient")
            message = data.get("message")
            print(f"{username} to {recipient}: {message}")
            
            # Send message to the recipient if they are connected
            if recipient in connections:
                await connections[recipient].send_text(f"{username}: {message}")
            
            # Do not send the message back to the sender if the recipient is the same
            if recipient != username:
                await websocket.send_text(f"You: {message}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up and remove the user from connections on disconnect
        del connections[username]
        print(f"{username} disconnected")
