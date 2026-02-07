const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const micBtn = document.getElementById('mic-btn');
const chatHistory = document.getElementById('chat-history');
const statusIndicator = document.getElementById('status-indicator');

let socket;
let isConnected = false;
let isListening = false;

// Initialize WebSocket
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        isConnected = true;
        updateStatus('Online', 'status-online');
        addSystemMessage("Connected to JARVIS core.");
    };

    socket.onclose = () => {
        isConnected = false;
        updateStatus('Offline', 'status-offline');
        addSystemMessage("Connection lost. Reconnecting in 3s...");
        setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (error) => {
        console.error('WebSocket Error:', error);
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
}

function updateStatus(text, className) {
    statusIndicator.textContent = text;
    statusIndicator.className = '';
    statusIndicator.classList.add(className);
}

function handleMessage(data) {
    if (data.type === 'response') {
        if (data.sender === 'user') {
            addMessage(data.content, 'user');
        } else {
            addMessage(data.content, 'ai');
        }
    } else if (data.type === 'voice_status') {
        isListening = data.listening;
        updateMicButton();
    }
}

function addMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);

    const bubble = document.createElement('div');
    bubble.classList.add('bubble');
    bubble.textContent = text;

    msgDiv.appendChild(bubble);
    chatHistory.appendChild(msgDiv);

    // Scroll to bottom
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function addSystemMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', 'system');

    const bubble = document.createElement('div');
    bubble.classList.add('bubble');
    bubble.textContent = text;

    msgDiv.appendChild(bubble);
    chatHistory.appendChild(msgDiv);
}

function sendMessage() {
    const text = messageInput.value.trim();
    if (text && isConnected) {
        socket.send(JSON.stringify({
            type: 'command',
            content: text
        }));
        // User message is echoed back by backend usually, but we can add optimistic UI if needed.
        // For now, let's rely on backend 'response' with sender='user' if built-in, 
        // OR just add it locally.
        // Looking at main.py: process_command doesn't broadcast 'user' message back, 
        // BUT listen() does. 
        // Let's add it locally for text input.
        addMessage(text, 'user');
        messageInput.value = '';
    }
}

function toggleVoice() {
    if (isConnected) {
        socket.send(JSON.stringify({
            type: 'toggle_voice'
        }));
        // Optimistic toggle
        micBtn.classList.toggle('active');
    }
}

function updateMicButton() {
    if (isListening) {
        micBtn.classList.add('active');
    } else {
        micBtn.classList.remove('active');
    }
}

// Event Listeners
sendBtn.addEventListener('click', sendMessage);

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

micBtn.addEventListener('click', toggleVoice);

// Start connection
connectWebSocket();
