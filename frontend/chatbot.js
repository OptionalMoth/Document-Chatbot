// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const fileInput = document.getElementById('fileInput');
const dropArea = document.getElementById('dropArea');
const fileList = document.getElementById('fileList');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const loadingOverlay = document.getElementById('loadingOverlay');
const cmsContent = document.getElementById('cmsContent');
const cmsSource = document.getElementById('cmsSource');

// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8000';

// State
let selectedFiles = [];
let isProcessing = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateStatus('ready', 'Ready');
    setupEventListeners();
    checkInitialHealth();
});

// Event Listeners
function setupEventListeners() {
    // Enter key to send message
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // File selection
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    dropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropArea.style.borderColor = '#667eea';
        dropArea.style.background = '#f7fafc';
    });
    
    dropArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropArea.style.borderColor = '#cbd5e0';
        dropArea.style.background = 'white';
    });
    
    dropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dropArea.style.borderColor = '#cbd5e0';
        dropArea.style.background = 'white';
        
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelect();
        }
    });
}

// Handle file selection
function handleFileSelect() {
    selectedFiles = Array.from(fileInput.files);
    updateFileList();
}

// Update file list display
function updateFileList() {
    if (selectedFiles.length === 0) {
        fileList.innerHTML = '<p class="no-files">No files selected</p>';
        return;
    }
    
    fileList.innerHTML = '';
    selectedFiles.forEach((file, index) => {
        const fileSize = formatFileSize(file.size);
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-info">
                <i class="fas fa-file file-icon"></i>
                <span class="file-name">${escapeHtml(file.name)}</span>
                <span class="file-size">(${fileSize})</span>
            </div>
            <button class="btn-remove" onclick="removeFile(${index})" title="Remove file">
                <i class="fas fa-times"></i>
            </button>
        `;
        fileList.appendChild(fileItem);
    });
}

// Remove file from list
function removeFile(index) {
    selectedFiles.splice(index, 1);
    
    // Update the file input
    const dataTransfer = new DataTransfer();
    selectedFiles.forEach(file => dataTransfer.items.add(file));
    fileInput.files = dataTransfer.files;
    
    updateFileList();
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Upload files to backend
async function uploadFiles() {
    if (selectedFiles.length === 0) {
        showMessage('Please select files to upload.', 'bot');
        return;
    }
    
    isProcessing = true;
    showLoading(true);
    updateStatus('processing', 'Uploading files...');
    
    let successCount = 0;
    let errorCount = 0;
    
    // Show single upload start message
    showMessage(`📤 Uploading ${selectedFiles.length} file(s)...`, 'system');
    
    for (const file of selectedFiles) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                successCount++;
            } else {
                showMessage(`❌ Failed to upload ${escapeHtml(file.name)}: ${escapeHtml(data.detail || 'Unknown error')}`, 'bot');
                errorCount++;
            }
        } catch (error) {
            console.error('Upload error:', error);
            showMessage(`❌ Error uploading ${escapeHtml(file.name)}: ${escapeHtml(error.message)}`, 'bot');
            errorCount++;
        }
    }
    
    // Clear file list after upload
    selectedFiles = [];
    fileInput.value = '';
    updateFileList();
    
    showLoading(false);
    isProcessing = false;
    updateStatus('ready', 'Ready');
    
    // Show summary message
    if (successCount > 0) {
        showMessage(`✅ Upload completed: ${successCount} successful, ${errorCount} failed`, 'bot');
    } else if (errorCount > 0) {
        showMessage('❌ All uploads failed. Please check your files and try again.', 'bot');
    }
}

// Import CMS content
async function importCMS() {
    const content = cmsContent.value.trim();
    const source = cmsSource.value.trim() || 'CMS Import';
    
    if (!content) {
        showMessage('Please enter CMS content to import.', 'bot');
        return;
    }
    
    showLoading(true);
    updateStatus('processing', 'Importing CMS content...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/import-cms`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: content,
                source: source,
                metadata: {
                    imported_at: new Date().toISOString(),
                    type: 'cms_content'
                }
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(`✅ CMS content imported from "${escapeHtml(source)}"! (${data.chunks} chunks processed)`, 'bot');
            cmsContent.value = '';
            cmsSource.value = '';
        } else {
            showMessage(`❌ Failed to import CMS content: ${escapeHtml(data.detail || 'Unknown error')}`, 'bot');
        }
    } catch (error) {
        console.error('CMS import error:', error);
        showMessage(`❌ Error importing CMS content: ${escapeHtml(error.message)}`, 'bot');
    }
    
    showLoading(false);
    updateStatus('ready', 'Ready');
}

// Send chat message
async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isProcessing) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    chatInput.value = '';
    
    // Show typing indicator
    const typingIndicator = addMessage('Thinking...', 'bot typing');
    
    try {
        updateStatus('processing', 'Processing query...');
        
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: message })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        typingIndicator.remove();
        
        if (response.ok) {
            // Add bot response
            addMessage(data.answer, 'bot');
            
            // Add sources if available
            if (data.sources && data.sources.length > 0) {
                const sourcesHtml = data.sources.map(source => `
                    <div class="source-item">
                        <div class="source-text">"${escapeHtml(source.text)}"</div>
                        <div class="source-meta">
                            <span>From: ${escapeHtml(source.source)}</span>
                            <span>Relevance: ${(source.score * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                `).join('');
                
                const sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'sources';
                sourcesDiv.innerHTML = `<h4>📚 Sources</h4>${sourcesHtml}`;
                
                const lastMessage = chatMessages.lastElementChild.querySelector('.message-content');
                lastMessage.appendChild(sourcesDiv);
            }
        } else {
            addMessage(`❌ Error: ${escapeHtml(data.detail || 'Failed to get response')}`, 'bot');
        }
    } catch (error) {
        console.error('Chat error:', error);
        typingIndicator.remove();
        addMessage('❌ Unable to connect to the server. Please make sure the backend is running.', 'bot');
        updateStatus('error', 'Connection Error');
    }
    
    updateStatus('ready', 'Ready');
}

// Add message to chat
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-text">${escapeHtml(text)}</div>
            <div class="message-time">${time}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

// Show system message
function showMessage(text, sender) {
    addMessage(text, sender);
}

// Update status indicator
function updateStatus(state, text) {
    statusText.textContent = text;
    
    switch(state) {
        case 'ready':
            statusDot.style.background = '#48bb78';
            break;
        case 'processing':
            statusDot.style.background = '#ed8936';
            break;
        case 'error':
            statusDot.style.background = '#f56565';
            break;
    }
}

// Show/hide loading overlay
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// Check backend health
async function checkHealth() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(`${API_BASE_URL}/health`, {
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        return response.ok;
    } catch (error) {
        console.warn('Health check failed:', error.message);
        return false;
    }
}

// Check health on startup
async function checkInitialHealth() {
    const isHealthy = await checkHealth();
    if (!isHealthy) {
        showMessage('⚠️ Backend server is not responding. Please make sure the backend is running on http://127.0.0.1:8000', 'bot');
        updateStatus('error', 'Disconnected');
    }
}

// Update health status periodically
async function checkAndUpdateStatus() {
    const isHealthy = await checkHealth();
    if (isHealthy && statusText.textContent.includes('Disconnected')) {
        updateStatus('ready', 'Connected');
    } else if (!isHealthy) {
        updateStatus('error', 'Disconnected');
    }
}

// Start periodic health checks
setInterval(checkAndUpdateStatus, 10000);

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}