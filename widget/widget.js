/**
 * AI Receptionist Chat Widget
 */
(function() {
    'use strict';

    class ChatWidget {
        constructor(config) {
            this.config = {
                apiUrl: config.apiUrl || 'http://localhost:8000',
                businessId: config.businessId || 'restaurant_001',
                position: config.position || 'bottom-right',
                primaryColor: config.primaryColor || '#007bff',
                ...config
            };
            
            this.isOpen = false;
            this.ws = null;
            this.init();
        }

        init() {
            this.createWidget();
            this.attachStyles();
            this.connectWebSocket();
        }

        createWidget() {
            // Create widget container
            this.container = document.createElement('div');
            this.container.id = 'ai-receptionist-widget';
            this.container.className = 'ai-receptionist-widget';

            // Create chat button
            this.button = document.createElement('div');
            this.button.className = 'ai-receptionist-button';
            this.button.innerHTML = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
            `;
            this.button.addEventListener('click', () => this.toggleChat());

            // Create chat window
            this.chatWindow = document.createElement('div');
            this.chatWindow.className = 'ai-receptionist-window';
            this.chatWindow.innerHTML = `
                <div class="ai-receptionist-header">
                    <h3>AI Receptionist</h3>
                    <button class="ai-receptionist-close">&times;</button>
                </div>
                <div class="ai-receptionist-messages"></div>
                <div class="ai-receptionist-input-container">
                    <input type="text" class="ai-receptionist-input" placeholder="Type your message...">
                    <button class="ai-receptionist-send">Send</button>
                </div>
            `;

            this.container.appendChild(this.button);
            this.container.appendChild(this.chatWindow);

            // Add to page
            document.body.appendChild(this.container);

            // Event listeners
            const closeBtn = this.chatWindow.querySelector('.ai-receptionist-close');
            closeBtn.addEventListener('click', () => this.toggleChat());

            const sendBtn = this.chatWindow.querySelector('.ai-receptionist-send');
            const input = this.chatWindow.querySelector('.ai-receptionist-input');
            sendBtn.addEventListener('click', () => this.sendMessage());
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });

            // Initial greeting
            this.addMessage('assistant', 'Hello! How can I help you today?');
        }

        attachStyles() {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = `${this.config.apiUrl}/widget/widget.css`;
            document.head.appendChild(link);
        }

        connectWebSocket() {
            const wsUrl = this.config.apiUrl.replace('http', 'ws') + '/api/chat/ws';
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('Chat widget connected');
                this.ws.send(JSON.stringify({
                    type: 'init',
                    business_id: this.config.businessId
                }));
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'message') {
                    this.addMessage('assistant', data.text);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            this.ws.onclose = () => {
                console.log('Chat widget disconnected');
                // Reconnect after 3 seconds
                setTimeout(() => this.connectWebSocket(), 3000);
            };
        }

        toggleChat() {
            this.isOpen = !this.isOpen;
            this.container.classList.toggle('open', this.isOpen);
        }

        addMessage(role, text) {
            const messagesContainer = this.chatWindow.querySelector('.ai-receptionist-messages');
            const message = document.createElement('div');
            message.className = `ai-receptionist-message ai-receptionist-message-${role}`;
            message.textContent = text;
            messagesContainer.appendChild(message);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        sendMessage() {
            const input = this.chatWindow.querySelector('.ai-receptionist-input');
            const text = input.value.trim();
            
            if (!text) return;

            // Add user message
            this.addMessage('user', text);
            input.value = '';

            // Send via WebSocket
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'message',
                    text: text,
                    business_id: this.config.businessId
                }));
            } else {
                // Fallback to HTTP
                this.sendMessageHTTP(text);
            }
        }

        async sendMessageHTTP(text) {
            try {
                const response = await fetch(`${this.config.apiUrl}/api/chat/message`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        text: text,
                        business_id: this.config.businessId
                    })
                });

                const data = await response.json();
                if (data.response) {
                    this.addMessage('assistant', data.response);
                }
            } catch (error) {
                console.error('Error sending message:', error);
                this.addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
            }
        }
    }

    // Auto-initialize if config is provided
    if (window.AIReceptionistConfig) {
        window.AIReceptionist = new ChatWidget(window.AIReceptionistConfig);
    }

    // Export for manual initialization
    window.AIReceptionistWidget = ChatWidget;
})();


