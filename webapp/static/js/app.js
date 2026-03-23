// State management
let currentFile = null;
let currentConversionMode = 'auto';
let currentInputMode = 'upload';
let currentTextContent = null;

// I2C Log Parser state
let currentI2cFile = null;

document.addEventListener('DOMContentLoaded', function() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadZone && fileInput) {
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
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });
    }
    
    document.querySelectorAll('input[name="conversionMode"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            currentConversionMode = e.target.value;
        });
    });
    
    initTextInput();
});

function switchInputMode(mode) {
    currentInputMode = mode;
    const uploadBtn = document.getElementById('mode-upload');
    const pasteBtn = document.getElementById('mode-paste');
    const uploadZoneEl = document.getElementById('uploadZone');
    const textInputZone = document.getElementById('textInputZone');
    const fileInfo = document.getElementById('fileInfo');
    
    if (mode === 'upload') {
        if (uploadBtn) uploadBtn.classList.add('active');
        if (pasteBtn) pasteBtn.classList.remove('active');
        if (uploadZoneEl) uploadZoneEl.style.display = 'block';
        if (textInputZone) textInputZone.style.display = 'none';
        if (fileInfo) fileInfo.style.display = 'none';
        currentTextContent = null;
    } else {
        if (pasteBtn) pasteBtn.classList.add('active');
        if (uploadBtn) uploadBtn.classList.remove('active');
        if (uploadZoneEl) uploadZoneEl.style.display = 'none';
        if (textInputZone) textInputZone.style.display = 'block';
        if (fileInfo) fileInfo.style.display = 'none';
        currentFile = null;
        
        const textInput = document.getElementById('textInput');
        if (textInput) {
            setTimeout(() => {
                textInput.focus();
            }, 100);
        }
    }
    
    const convertBtn = document.getElementById('convertBtn');
    if (convertBtn) {
        convertBtn.disabled = true;
    }
}

function initTextInput() {
    const textInput = document.getElementById('textInput');
    if (textInput) {
        textInput.addEventListener('input', (e) => {
            const content = e.target.value.trim();
            const charCount = document.getElementById('textCharCount');
            
            if (charCount) {
                charCount.textContent = content.length;
            }
            
            const convertBtn = document.getElementById('convertBtn');
            if (content.length > 0) {
                currentTextContent = content;
                if (convertBtn) convertBtn.disabled = false;
                
                const fileFormat = document.getElementById('fileFormat');
                const detectedFormat = detectFormatFromText(content);
                if (fileFormat && currentInputMode === 'paste') {
                    fileFormat.textContent = detectedFormat.toUpperCase();
                    const formatColors = {
                        'VENDOR': 'linear-gradient(135deg, #ff006e, #ff6b35)',
                        'INI': 'linear-gradient(135deg, #00f0ff, #0088ff)',
                        'FREERTOS': 'linear-gradient(135deg, #00ff88, #00cc6a)',
                        'ADI_FAE': 'linear-gradient(135deg, #9d4edd, #ff00ff)',
                        'COM_LOG': 'linear-gradient(135deg, #ffd700, #ff8c00)'
                    };
                    fileFormat.style.background = formatColors[detectedFormat.toUpperCase()] || formatColors.INI;
                    fileFormat.style.color = '#0a0a0f';
                }
            } else {
                currentTextContent = null;
                if (convertBtn) convertBtn.disabled = true;
            }
        });
    }
}

function detectFormatFromText(content) {
    const lines = content.split('\n').slice(0, 20);
    const contentSample = lines.join('\n');
    const searchableContent = content;
    
    if (/\[fd\]\d+\.\d+\.\d+:\[C\d+\]\[I\]\[[^\]]+\]:i2c-\d+\s+write\s+addr:/.test(searchableContent)) {
        return 'com_log';
    }
    if (/\[(SERDES|Sensor)\]:i2c-\d+/.test(searchableContent)) {
        return 'ti960_log';
    }
    if (contentSample.includes('I2CADDR=') || contentSample.includes('MODE=')) {
        return 'ini';
    }
    if (contentSample.includes('i2cwrite') || contentSample.includes('i2cread')) {
        return 'freertos';
    }
    
    for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('//') && !trimmed.startsWith('#')) {
            if (trimmed.startsWith('0x')) {
                const parts = trimmed.replace(/,$/, '').split(',').map(p => p.trim());
                if (parts.length === 5 && parts.every(p => p.startsWith('0x'))) {
                    return 'adi_fae';
                }
            }
        }
    }
    
    for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#')) {
            if (trimmed.length === 6 && trimmed.startsWith('0x')) {
                return 'vendor';
            }
            if (trimmed.includes(',') && trimmed.startsWith('0x')) {
                return 'vendor';
            }
        }
    }
    
    return 'freertos';
}

async function handleFile(file) {
    const allowedTypes = ['txt', 'ini', 'cfg', 'md', 'log', 'cpp'];
    const fileExt = file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExt)) {
        showToast('Invalid file type. Please upload .txt, .ini, .cfg, .md, .log, or .cpp files', 'error');
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
        'FREERTOS': 'linear-gradient(135deg, #00ff88, #00cc6a)',
        'ADI_FAE': 'linear-gradient(135deg, #9d4edd, #ff00ff)',
        'COM_LOG': 'linear-gradient(135deg, #ffd700, #ff8c00)'
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
    
    document.getElementById('resultSection').style.display = 'none';
}

function removeTextContent() {
    currentTextContent = null;
    
    const textInputZone = document.getElementById('textInputZone');
    const textInput = document.getElementById('textInput');
    const charCount = document.getElementById('textCharCount');
    
    textInput.value = '';
    if (charCount) {
        charCount.textContent = '0';
    }
    textInputZone.style.display = 'none';
    uploadZone.style.display = 'block';
    
    document.getElementById('convertBtn').disabled = true;
    document.getElementById('resultSection').style.display = 'none';
}

async function convertFile() {
    if (!currentFile && !currentTextContent) {
        showToast('Please upload a file or paste text first', 'error');
        return;
    }
    
    const convertBtn = document.getElementById('convertBtn');
    convertBtn.classList.add('loading');
    convertBtn.disabled = true;
    
    try {
        showToast('Converting...', 'info');
        
        let response;
        if (currentInputMode === 'paste' && currentTextContent) {
            response = await fetch('/api/convert-text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: currentTextContent,
                    mode: currentConversionMode
                })
            });
        } else {
            response = await fetch('/api/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: currentFile.filename,
                    mode: currentConversionMode
                })
            });
        }
        
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

// ============================================
// I2C Log Parser Functions
// ============================================

const i2cUploadZone = document.getElementById('i2cUploadZone');
const i2cFileInput = document.getElementById('i2cFileInput');

if (i2cUploadZone) {
    i2cUploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        i2cUploadZone.classList.add('dragover');
    });

    i2cUploadZone.addEventListener('dragleave', () => {
        i2cUploadZone.classList.remove('dragover');
    });

    i2cUploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        i2cUploadZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleI2cFile(files[0]);
        }
    });
}

if (i2cFileInput) {
    i2cFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleI2cFile(e.target.files[0]);
        }
    });
}

async function handleI2cFile(file) {
    const allowedTypes = ['txt', 'md', 'log'];
    const fileExt = file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExt)) {
        showToast('Invalid file type. Please upload .txt, .md, or .log files', 'error');
        return;
    }
    
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
            currentI2cFile = result;
            displayI2cFileInfo(result);
            showToast('File uploaded successfully', 'success');
        } else {
            showToast(`Upload failed: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast(`Upload error: ${error.message}`, 'error');
    }
}

function displayI2cFileInfo(fileData) {
    const fileInfo = document.getElementById('i2cFileInfo');
    const fileName = document.getElementById('i2cFileName');
    const fileSize = document.getElementById('i2cFileSize');
    const uploadZone = document.getElementById('i2cUploadZone');
    
    fileName.textContent = fileData.original_filename;
    fileSize.textContent = formatFileSize(fileData.file_size);
    
    uploadZone.style.display = 'none';
    fileInfo.style.display = 'flex';
    
    document.getElementById('parseBtn').disabled = false;
}

function removeI2cFile() {
    currentI2cFile = null;
    
    const fileInfo = document.getElementById('i2cFileInfo');
    const uploadZone = document.getElementById('i2cUploadZone');
    
    fileInfo.style.display = 'none';
    uploadZone.style.display = 'block';
    
    document.getElementById('i2cFileInput').value = '';
    document.getElementById('parseBtn').disabled = true;
    
    document.getElementById('i2cResultSection').style.display = 'none';
}

async function parseI2cLog() {
    if (!currentI2cFile) {
        showToast('Please upload a file first', 'error');
        return;
    }
    
    const parseBtn = document.getElementById('parseBtn');
    parseBtn.classList.add('loading');
    parseBtn.disabled = true;
    
    try {
        showToast('Parsing I2C log...', 'info');
        
        const response = await fetch('/api/parse-i2c-log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: currentI2cFile.filename
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayI2cResult(result);
            showToast('Parsing successful!', 'success');
        } else {
            showToast(`Parsing failed: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast(`Parsing error: ${error.message}`, 'error');
    } finally {
        parseBtn.classList.remove('loading');
        parseBtn.disabled = false;
    }
}

function displayI2cResult(result) {
    const resultSection = document.getElementById('i2cResultSection');
    const outputFilename = document.getElementById('i2cOutputFilename');
    const conversionMessage = document.getElementById('i2cConversionMessage');
    
    outputFilename.textContent = result.output_filename;
    conversionMessage.textContent = result.message;
    
    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    window.currentI2cDownloadUrl = result.download_url;
    window.currentI2cOutputFilename = result.output_filename;
}

function downloadI2cFile() {
    if (window.currentI2cDownloadUrl) {
        window.open(window.currentI2cDownloadUrl, '_blank');
    }
}

async function previewI2cFile() {
    if (!window.currentI2cOutputFilename) {
        showToast('No file to preview', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/preview/${window.currentI2cOutputFilename}`);
        const result = await response.json();
        
        if (result.success) {
            const previewCard = document.getElementById('i2cPreviewCard');
            const previewContent = document.getElementById('i2cPreviewContent');
            
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

function closeI2cPreview() {
    document.getElementById('i2cPreviewCard').style.display = 'none';
}

// Mode switching function
function switchMode(mode) {
    const converterSection = document.querySelector('.converter-section');
    const i2cParserSection = document.getElementById('i2cParserSection');
    const tabConverter = document.getElementById('tab-converter');
    const tabI2cParser = document.getElementById('tab-i2c-parser');
    
    if (mode === 'converter') {
        converterSection.style.display = 'block';
        i2cParserSection.style.display = 'none';
        tabConverter.classList.add('active');
        tabI2cParser.classList.remove('active');
    } else if (mode === 'i2c-parser') {
        converterSection.style.display = 'none';
        i2cParserSection.style.display = 'block';
        tabConverter.classList.remove('active');
        tabI2cParser.classList.add('active');
    }
}
