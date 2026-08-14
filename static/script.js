// Frontend script for PII Redaction Tool

document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const fileDisplay = document.getElementById('fileDisplay');
    const fileNameEl = document.getElementById('fileName');
    const fileSizeEl = document.getElementById('fileSize');
    const removeFileBtn = document.getElementById('removeFileBtn');
    const redactBtn = document.getElementById('redactBtn');
    
    const uploadView = document.getElementById('uploadView');
    const loadingView = document.getElementById('loadingView');
    const resultsView = document.getElementById('resultsView');
    const errorView = document.getElementById('errorView');
    
    const errorTitle = document.getElementById('errorTitle');
    const errorMessage = document.getElementById('errorMessage');
    
    const statDetected = document.getElementById('statDetected');
    const statRedacted = document.getElementById('statRedacted');
    
    const downloadBtn = document.getElementById('downloadBtn');
    const resetBtn = document.getElementById('resetBtn');
    const errorResetBtn = document.getElementById('errorResetBtn');

    let selectedFile = null;
    let redactedBlob = null;
    let redactedFilename = '';

    // Drag & Drop
    dropzone.addEventListener('click', () => fileInput.click());
    
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        if (!file.name.toLowerCase().endsWith('.docx')) {
            showError('Invalid file type', 'Only Word documents (.docx) are supported.');
            return;
        }
        selectedFile = file;
        fileNameEl.textContent = file.name;
        fileSizeEl.textContent = (file.size / 1024).toFixed(1) + ' KB';
        
        dropzone.classList.add('hidden');
        fileDisplay.classList.remove('hidden');
        redactBtn.disabled = false;
        
        // Hide error if visible
        errorView.classList.add('hidden');
    }

    removeFileBtn.addEventListener('click', () => {
        clearFileSelection();
    });

    function clearFileSelection() {
        selectedFile = null;
        fileInput.value = '';
        fileDisplay.classList.add('hidden');
        dropzone.classList.remove('hidden');
        redactBtn.disabled = true;
    }

    // Submit Redaction
    redactBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        // Prevent double submission
        redactBtn.disabled = true;
        uploadView.classList.add('hidden');
        loadingView.classList.remove('hidden');

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/redact', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                let detailMsg = 'The server encountered an error processing your file.';
                if (response.status === 413) {
                    detailMsg = 'The uploaded file exceeds the 15 MB size limit.';
                } else if (response.status === 400) {
                    detailMsg = 'The file format is invalid or corrupted.';
                }
                
                try {
                    const jsonErr = await response.json();
                    if (jsonErr && jsonErr.detail) {
                        detailMsg = jsonErr.detail;
                    }
                } catch(e) {}
                
                throw new Error(detailMsg);
            }

            // Read exposed stats headers
            const detected = response.headers.get('X-Candidates-Detected') || '0';
            const accepted = response.headers.get('X-Candidates-Accepted') || '0';

            // Retrieve DOCX blob
            redactedBlob = await response.blob();
            
            const originalBase = selectedFile.name.substring(0, selectedFile.name.lastIndexOf('.'));
            redactedFilename = `${originalBase}_redacted.docx`;

            // Render stats
            statDetected.textContent = detected;
            statRedacted.textContent = accepted;

            loadingView.classList.add('hidden');
            resultsView.classList.remove('hidden');

        } catch (err) {
            showError('Something went wrong', err.message);
        }
    });

    // Download Redacted File
    downloadBtn.addEventListener('click', () => {
        if (!redactedBlob) return;
        
        const url = window.URL.createObjectURL(redactedBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = redactedFilename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    });

    // Reset Forms
    resetBtn.addEventListener('click', () => {
        clearFileSelection();
        redactedBlob = null;
        redactedFilename = '';
        resultsView.classList.add('hidden');
        uploadView.classList.remove('hidden');
    });

    errorResetBtn.addEventListener('click', () => {
        clearFileSelection();
        errorView.classList.add('hidden');
        uploadView.classList.remove('hidden');
    });

    function showError(title, msg) {
        errorTitle.textContent = title;
        errorMessage.textContent = msg;
        
        loadingView.classList.add('hidden');
        uploadView.classList.add('hidden');
        resultsView.classList.add('hidden');
        errorView.classList.remove('hidden');
    }
});
