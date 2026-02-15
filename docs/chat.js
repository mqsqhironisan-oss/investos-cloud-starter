/**
 * InvestOS AI Chat JavaScript
 * - Fetches context data from CSV files
 * - Sends messages to Cloudflare Workers API endpoint
 * - Displays chat history with XSS protection
 */

// Configuration
const CHAT_API_URL = window.INVESTOS_CHAT_API || '/api/chat';

// Context data cache
let contextData = {
    regime: null,
    theme_strength: null,
    signals: null,
    orders: null,
    weights: null
};

// DOM elements
let messagesContainer, userInput, sendBtn, loadingIndicator;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    messagesContainer = document.getElementById('chat-messages');
    userInput = document.getElementById('user-input');
    sendBtn = document.getElementById('send-btn');
    loadingIndicator = document.getElementById('loading');

    // Event listeners
    sendBtn.addEventListener('click', handleSend);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // Load context data
    loadContextData();
});

/**
 * Load context data from CSV files
 * Fails silently - chat still works with empty context
 */
async function loadContextData() {
    const files = {
        regime: 'data/regime.csv',
        theme_strength: 'data/theme_strength.csv',
        signals: 'data/signals.csv',
        orders: 'data/orders.csv',
        weights: 'data/weights_champion.csv'
    };

    for (const [key, path] of Object.entries(files)) {
        try {
            const response = await fetch(path);
            if (response.ok) {
                const text = await response.text();
                contextData[key] = parseCSV(text);
            }
        } catch (error) {
            console.warn(`Failed to load ${path}:`, error);
            contextData[key] = null;
        }
    }

    console.log('Context data loaded:', Object.keys(contextData).filter(k => contextData[k]));
}

/**
 * Simple CSV parser - returns last row as object
 */
function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) return null;

    const headers = lines[0].split(',').map(h => h.trim());
    const lastLine = lines[lines.length - 1].split(',').map(v => v.trim());

    const result = {};
    headers.forEach((header, i) => {
        result[header] = lastLine[i] || '';
    });

    return result;
}

/**
 * Handle send button click
 */
async function handleSend() {
    const message = userInput.value.trim();
    if (!message) return;

    // Clear input and disable during processing
    userInput.value = '';
    sendBtn.disabled = true;
    loadingIndicator.style.display = 'block';

    // Add user message to chat
    addMessage('user', message);

    try {
        // Send to API
        const response = await fetch(CHAT_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                context: contextData
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        const reply = data.reply || 'No response from AI';

        // Add AI response to chat
        addMessage('assistant', reply);

    } catch (error) {
        console.error('Chat error:', error);
        addMessage('assistant', `エラーが発生しました: ${error.message}\n\nCloudflare Workersエンドポイントの設定を確認してください。`);
    } finally {
        // Re-enable input
        sendBtn.disabled = false;
        loadingIndicator.style.display = 'none';
        userInput.focus();
    }
}

/**
 * Add message to chat with XSS protection
 * @param {string} role - 'user' or 'assistant'
 * @param {string} content - Message content (will be escaped)
 */
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // Format content with basic markdown-like formatting
    const formatted = formatMessage(content);
    contentDiv.innerHTML = formatted;

    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Format message content with XSS protection
 * Supports basic markdown: **bold**, `code`, and line breaks
 */
function formatMessage(text) {
    // Escape HTML first to prevent XSS
    const escaped = escapeHTML(text);

    // Apply simple markdown-like formatting with safe replacements
    // These patterns are designed to be XSS-safe as the text is already escaped
    let formatted = escaped
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')  // **bold**
        .replace(/`(.+?)`/g, '<code>$1</code>')  // `code`
        .replace(/\n/g, '<br>');  // line breaks

    return formatted;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
