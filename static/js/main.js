// Main JavaScript file for Agriculture Hub

document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Chatbot functionality
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-btn');

    if (chatMessages && userInput && sendButton) {
        // Function to add a message to the chat
        window.addMessage = function(message, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;

            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';

            const messageParagraph = document.createElement('p');
            messageParagraph.textContent = message;

            messageContent.appendChild(messageParagraph);
            messageDiv.appendChild(messageContent);
            chatMessages.appendChild(messageDiv);

            // Scroll to the bottom of the chat
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // Function to show typing indicator
        window.showTypingIndicator = function() {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message bot typing-indicator';
            typingDiv.id = 'typing-indicator';

            const typingContent = document.createElement('div');
            typingContent.className = 'message-content';

            const typingDots = document.createElement('div');
            typingDots.className = 'typing-dots';
            typingDots.innerHTML = '<span>.</span><span>.</span><span>.</span>';

            typingContent.appendChild(typingDots);
            typingDiv.appendChild(typingContent);
            chatMessages.appendChild(typingDiv);

            // Scroll to the bottom of the chat
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // Function to remove typing indicator
        window.removeTypingIndicator = function() {
            const typingIndicator = document.getElementById('typing-indicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
        }

        // Function to send a message to the backend
        window.sendMessage = async function(message) {
            if (!message.trim()) return;

            // Add user message to chat
            window.addMessage(message, true);

            // Clear input field
            userInput.value = '';

            // Show typing indicator
            window.showTypingIndicator();

            try {
                // Send message to backend
                const response = await fetch('/chatbot/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: message })
                });

                // Remove typing indicator after a short delay to simulate thinking
                setTimeout(() => {
                    window.removeTypingIndicator();

                    // Process the response
                    response.json().then(data => {
                        if (response.ok) {
                            // Add bot response to chat
                            window.addMessage(data.response, false);
                        } else {
                            // Add error message with details if available
                            if (data.debug && data.error_details) {
                                window.addMessage(`Error: ${data.error_details}`, false);
                                console.error('Detailed error:', data.error_details);
                            } else {
                                window.addMessage(data.response || 'Sorry, I encountered an error. Please try again.', false);
                                console.error('Error:', data.error || 'Unknown error');
                            }
                        }
                    }).catch(error => {
                        // Add error message if JSON parsing fails
                        window.addMessage('Sorry, I encountered an error processing the response. Please try again.', false);
                        console.error('JSON parsing error:', error);
                    });
                }, 1000);
            } catch (error) {
                // Remove typing indicator
                window.removeTypingIndicator();

                // Add error message
                window.addMessage('Sorry, I encountered an error connecting to the server. Please try again.', false);
                console.error('Network error:', error);
            }
        }

        // Event listener for send button
        sendButton.addEventListener('click', function() {
            window.sendMessage(userInput.value);
        });

        // Event listener for Enter key
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                window.sendMessage(userInput.value);
            }
        });
    }

    // Function to handle suggestion chip clicks
    window.askQuestion = function(question) {
        if (userInput && window.sendMessage) {
            userInput.value = question;
            window.sendMessage(question);
        }
    };
});
