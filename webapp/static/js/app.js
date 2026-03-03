// State management
let currentFile = null;
let currentConversionMode = 'auto';

// Initialize upload zone
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');

// Drag and drop handlers
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

// File input change handler
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

// Mode selection handler
document.querySelectorAll('input[name="conversionMode"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        currentConversionMode = e.target.value;
    });
});

async function handleFile(file) {
    const allowedTypes = ['txt', 'ini', 'cfg'];
    const fileExt = file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExt)) {
        showToast('Invalid file type. Please upload .txt, .ini, or .cfg files', 'error');
        return;
    }
    
    // Upload file to server
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showToast('Uploading file...', 'info');
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentFile = result;
            displayFileInfo(result);
            showToast('File uploaded successfully', 'success');
        } else {
            showToast(`Upload failed: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast(`Upload error: ${error.message}`, 'error');
    }
}

function displayFileInfo(fileData) {
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileFormat = document.getElementById('fileFormat');
    const uploadZone = document.getElementById('uploadZone');
    
    fileName.textContent = fileData.original_filename;
    fileSize.textContent = formatFileSize(fileData.file_size);
    fileFormat.textContent = fileData.detected_format.toUpperCase();
    
    // Color-code format badges
    const formatColors = {
        'VENDOR': 'linear-gradient(135deg, #ff006e, #ff6b35)',
        'INI': 'linear-gradient(135deg, #00f0ff, #0088ff)',
        'FREERTOS': 'linear-gradient(135deg, #00ff88, #00cc6a)'
    };
    fileFormat.style.background = formatColors[fileData.detected_format.toUpperCase()] || formatColors.INI;
    fileFormat.style.color = '#0a0a0f';
    
    uploadZone.style.display = 'none';
    fileInfo.style.display = 'flex';
    
    // Enable convert button
    document.getElementById('convertBtn').disabled = false;
}

function removeFile() {
    currentFile = null;
    
    const fileInfo = document.getElementById('fileInfo');
    const uploadZone = document.getElementById('uploadZone');
    
    fileInfo.style.display = 'none';
    uploadZone.style.display = 'block';
    
    document.getElementById('fileInput').value = '';
    document.getElementById('convertBtn').disabled = true;
    
    // Hide result section if visible
    document.getElementById('resultSection').style.display = 'none';
}

async function convertFile() {
    if (!currentFile) {
        showToast('Please upload a file first', 'error');
        return;
    }
    
    const convertBtn = document.getElementById('convertBtn');
    convertBtn.classList.add('loading');
    convertBtn.disabled = true;
    
    try {
        showToast('Converting...', 'info');
        
        const response = await fetch('/api/convert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: currentFile.filename,
                mode: currentConversionMode
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayResult(result);
            showToast('Conversion successful!', 'success');
        } else {
            showToast(`Conversion failed: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast(`Conversion error: ${error.message}`, 'error');
    } finally {
        convertBtn.classList.remove('loading');
        convertBtn.disabled = false;
    }
}

function displayResult(result) {
    const resultSection = document.getElementById('resultSection');
    const outputFilename = document.getElementById('outputFilename');
    const conversionMessage = document.getElementById('conversionMessage');
    
    outputFilename.textContent = result.output_filename;
    conversionMessage.textContent = result.message;
    
    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Store download URL for later
    window.currentDownloadUrl = result.download_url;
    window.currentOutputFilename = result.output_filename;
}

function downloadFile() {
    if (window.currentDownloadUrl) {
        window.open(window.currentDownloadUrl, '_blank');
    }
}

async function previewFile() {
    if (!window.currentOutputFilename) {
        showToast('No file to preview', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/preview/${window.currentOutputFilename}`);
        const result = await response.json();
        
        if (result.success) {
            const previewCard = document.getElementById('previewCard');
            const previewContent = document.getElementById('previewContent');
            
            previewContent.textContent = result.content;
            previewCard.style.display = 'block';
            previewCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            showToast(`Preview failed: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast(`Preview error: ${error.message}`, 'error');
    }
}

function closePreview() {
    document.getElementById('previewCard').style.display = 'none';
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}
