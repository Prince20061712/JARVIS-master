const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const micBtn = document.getElementById('mic-btn');
const chatHistory = document.getElementById('chat-history');
const statusIndicator = document.getElementById('status-indicator');
const talkBtn = document.getElementById('talk-btn');
const danceBtn = document.getElementById('dance-btn');
const resetBtn = document.getElementById('reset-btn');

// Robot elements
const mouth = document.getElementById('mouth');
const speechBubble = document.getElementById('speech-bubble');
const bubbleText = document.getElementById('bubble-text');
const robotDisplay = document.getElementById('robot-display');
const ledProcessing = document.getElementById('led-processing');
const ledListening = document.getElementById('led-listening');
const ledError = document.getElementById('led-error');

// Audio elements
const speechAudio = document.getElementById('speech-audio');
const robotSound = document.getElementById('robot-sound');

let socket;
let isConnected = false;
let isListening = false;
let isTalking = false;
let isDancing = false;
let currentSpeech = null;
const speechQueue = [];

// Speech Synthesis
const synth = window.speechSynthesis;
let voices = [];

// Initialize WebSocket
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        isConnected = true;
        updateStatus('Online', 'status-online');
        addSystemMessage("Connected to JARVIS core.");
        robotSpeak("System online. Ready for commands.");
        setLED(ledProcessing, false);
    };

    socket.onclose = () => {
        isConnected = false;
        updateStatus('Offline', 'status-offline');
        addSystemMessage("Connection lost. Reconnecting in 3s...");
        setLED(ledError, true);
        setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (error) => {
        console.error('WebSocket Error:', error);
        setLED(ledError, true);
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleMessage(data);
        } catch (error) {
            console.error('Error parsing message:', error);
        }
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
            // Make robot speak the response
            if (data.content && !data.content.startsWith('(')) {
                robotSpeak(data.content);
            }
        }
    } else if (data.type === 'voice_status') {
        isListening = data.listening;
        setLED(ledListening, isListening);
        updateMicButton();
    } else if (data.type === 'processing') {
        setLED(ledProcessing, true);
    } else if (data.type === 'error') {
        robotSpeak("Error: " + data.message);
        setLED(ledError, true);
        setTimeout(() => setLED(ledError, false), 3000);
    }
}

function addMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);

    const bubble = document.createElement('div');
    bubble.classList.add('bubble');

    // Add timestamp
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    bubble.innerHTML = `<div>${text}</div><div class="message-time">${time}</div>`;

    // Add typing animation for AI messages
    if (sender === 'ai') {
        bubble.style.opacity = '0';
        setTimeout(() => {
            bubble.style.transition = 'opacity 0.3s';
            bubble.style.opacity = '1';
        }, 100);
    }

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
        addMessage(text, 'user');
        messageInput.value = '';
        setLED(ledProcessing, true);
    }
}

function toggleVoice() {
    if (isConnected) {
        socket.send(JSON.stringify({
            type: 'toggle_voice'
        }));
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

// Robot Functions
function robotSpeak(text) {
    if (!text || isTalking) {
        speechQueue.push(text);
        return;
    }

    isTalking = true;
    setLED(ledProcessing, true);

    // Notify backend that speech has started
    if (isConnected) {
        socket.send(JSON.stringify({
            type: 'speech_state',
            status: 'started'
        }));
    }

    // Show speech bubble
    bubbleText.textContent = text;
    speechBubble.classList.add('visible');

    // Start mouth animation
    mouth.classList.add('talking');

    // Use Web Speech API
    if (synth.speaking) {
        synth.cancel();
    }

    const utterance = new SpeechSynthesisUtterance(text);

    // Configure voice
    utterance.rate = 1;
    utterance.pitch = 1; // Normal pitch
    utterance.volume = 1;

    if (voices.length > 0) {
        // Updated voice selection logic - Priority: Daniel > UK English > US English
        let preferredVoice = voices.find(v => v.name.includes('Daniel'));

        if (!preferredVoice) {
            preferredVoice = voices.find(v => v.name.includes('UK English Male') || v.name.includes('Google UK English Male'));
        }

        if (!preferredVoice) {
            preferredVoice = voices.find(v => v.lang === 'en-GB' && v.name.includes('Male'));
        }

        if (!preferredVoice) {
            preferredVoice = voices.find(v => v.name.includes('Google') || v.name.includes('Microsoft'));
        }

        if (preferredVoice) {
            console.log("Using voice:", preferredVoice.name);
            utterance.voice = preferredVoice;
        }
    }

    utterance.onstart = () => {
        // Play robot sound effect
        playRobotSound();
    };

    utterance.onend = () => {
        finishSpeaking();
    };

    utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        finishSpeaking();
    };

    currentSpeech = utterance;
    synth.speak(utterance);
}

function finishSpeaking() {
    isTalking = false;
    setLED(ledProcessing, false);
    mouth.classList.remove('talking');

    // Notify backend that speech has finished
    if (isConnected) {
        socket.send(JSON.stringify({
            type: 'speech_state',
            status: 'finished'
        }));
    }

    // Hide speech bubble after delay
    setTimeout(() => {
        speechBubble.classList.remove('visible');
    }, 2000);

    // Process next in queue
    if (speechQueue.length > 0) {
        const nextText = speechQueue.shift();
        setTimeout(() => robotSpeak(nextText), 500);
    }
}

function playRobotSound() {
    // Create a simple robot sound
    const context = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = context.createOscillator();
    const gainNode = context.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(context.destination);

    oscillator.type = 'sawtooth';
    oscillator.frequency.setValueAtTime(200, context.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(100, context.currentTime + 0.1);

    gainNode.gain.setValueAtTime(0.1, context.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.1);

    oscillator.start();
    oscillator.stop(context.currentTime + 0.1);
}

function setLED(led, active) {
    if (active) {
        led.classList.add('active');
    } else {
        led.classList.remove('active');
    }
}

function danceRobot() {
    if (isDancing) return;

    isDancing = true;
    const robotContainer = document.querySelector('.robot-container');
    const wheels = document.querySelectorAll('.wheel');

    robotContainer.style.animation = 'robotDance 0.5s infinite';
    wheels.forEach(wheel => {
        wheel.style.animation = 'wheelSpin 1s infinite linear';
    });

    robotSpeak("Dancing mode activated!");

    // Stop after 5 seconds
    setTimeout(() => {
        robotContainer.style.animation = '';
        wheels.forEach(wheel => {
            wheel.style.animation = '';
        });
        isDancing = false;
        robotSpeak("Dance complete!");
    }, 5000);
}

function resetRobot() {
    // Stop any current animations
    const robotContainer = document.querySelector('.robot-container');
    const wheels = document.querySelectorAll('.wheel');

    robotContainer.style.animation = '';
    wheels.forEach(wheel => {
        wheel.style.animation = '';
    });

    // Clear speech
    if (synth.speaking) {
        synth.cancel();
    }

    // Reset states
    isTalking = false;
    isDancing = false;
    speechQueue.length = 0;

    // Reset LEDs
    setLED(ledProcessing, false);
    setLED(ledListening, false);
    setLED(ledError, false);

    // Hide speech bubble
    speechBubble.classList.remove('visible');
    mouth.classList.remove('talking');

    robotSpeak("System reset. All systems nominal.");
}

// Initialize speech synthesis voices
function loadVoices() {
    voices = synth.getVoices();

    // Some browsers need this event
    if (voices.length === 0) {
        synth.onvoiceschanged = () => {
            voices = synth.getVoices();
        };
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

talkBtn.addEventListener('click', () => {
    const phrases = [
        "Hello! I am JARVIS, your personal assistant.",
        "Systems are functioning normally.",
        "Ready to assist with your commands.",
        "The weather outside is optimal for operations.",
        "All systems are green. We are good to go."
    ];
    const randomPhrase = phrases[Math.floor(Math.random() * phrases.length)];
    robotSpeak(randomPhrase);
});

danceBtn.addEventListener('click', danceRobot);
resetBtn.addEventListener('click', resetRobot);

// Eye follow cursor effect
document.addEventListener('mousemove', (e) => {
    const eyes = document.querySelectorAll('.eye');
    const robotHead = document.querySelector('.robot-head');
    const rect = robotHead.getBoundingClientRect();

    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
    const distance = Math.min(5, Math.hypot(e.clientX - centerX, e.clientY - centerY) / 50);

    eyes.forEach(eye => {
        const offsetX = Math.cos(angle) * distance;
        const offsetY = Math.sin(angle) * distance;
        eye.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
    });
});

// Update display with time
function updateDisplay() {
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const displayText = robotDisplay.querySelector('.display-text');
    displayText.textContent = `J.A.R.V.I.S\n${timeString}`;
}

// Start connection and initialize
window.addEventListener('load', () => {
    connectWebSocket();
    loadVoices();
    updateDisplay();
    setInterval(updateDisplay, 60000); // Update time every minute

    // Initial robot greeting
    setTimeout(() => {
        if (isConnected) {
            robotSpeak("JARVIS online. Systems initialized and ready.");
        }
    }, 1000);
});

// Add message time styling
const style = document.createElement('style');
style.textContent = `
    .message-time {
        font-size: 0.7rem;
        opacity: 0.7;
        margin-top: 5px;
        text-align: right;
    }
    
    .message.ai .message-time {
        text-align: left;
    }
`;
document.head.appendChild(style);