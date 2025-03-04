let socket;

function connectWebSocket() {
    let username = document.getElementById("username").value;
    // Check the current protocol of the page (either http or https)
    let protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    socket = new WebSocket(`${protocol}${window.location.host}/ws/${username}`);
    
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
