
// Mobile QR Scanner using device camera
document.addEventListener('DOMContentLoaded', function() {
    const scanButton = document.getElementById('scanQrButton');
    const stopButton = document.getElementById('stopQrScan');
    const qrResult = document.getElementById('qrResult');
    const videoElement = document.getElementById('qrVideo');
    const resultContainer = document.getElementById('scanResultContainer');
    
    if (scanButton) {
        scanButton.addEventListener('click', function() {
            startQRScanner('qrVideo');
        });
    }
    
    if (stopButton) {
        stopButton.addEventListener('click', function() {
            stopQRScanner();
        });
    }
});

let videoStream = null;
let scanning = false;

async function startQRScanner(videoElementId) {
    const videoElement = document.getElementById(videoElementId);
    const resultElement = document.getElementById('qrResult');
    const scanButton = document.getElementById('scanQrButton');
    const stopButton = document.getElementById('stopQrScan');
    
    if (!videoElement) return;
    
    try {
        // Request camera access
        videoStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: "environment",
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        });
        
        // Show the video element
        videoElement.style.display = 'block';
        videoElement.srcObject = videoStream;
        videoElement.play();
        
        // Show stop button, hide scan button
        if (scanButton) scanButton.style.display = 'none';
        if (stopButton) stopButton.style.display = 'inline-block';
        
        // Start scanning
        scanning = true;
        scanQRCode(videoElement, resultElement);
        
    } catch (error) {
        console.error('Error accessing camera:', error);
        if (resultElement) {
            resultElement.innerHTML = `<div class="alert alert-danger">Error accessing camera: ${error.message}</div>`;
        }
    }
}

function stopQRScanner() {
    scanning = false;
    
    const videoElement = document.getElementById('qrVideo');
    const scanButton = document.getElementById('scanQrButton');
    const stopButton = document.getElementById('stopQrScan');
    
    // Stop video stream
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
    
    // Hide video element
    if (videoElement) {
        videoElement.srcObject = null;
        videoElement.style.display = 'none';
    }
    
    // Show scan button, hide stop button
    if (scanButton) scanButton.style.display = 'inline-block';
    if (stopButton) stopButton.style.display = 'none';
}

async function scanQRCode(videoElement, resultElement) {
    try {
        // Import jsQR library dynamically
        const jsQR = await importJsQR();
        
        // Create canvas to analyze video frames
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        
        // Set canvas dimensions to match video
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        
        // Scanning loop
        const scan = () => {
            if (!scanning) return;
            
            if (videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
                // Draw current video frame to canvas
                context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
                
                // Get image data for QR code detection
                const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
                
                // Detect QR code
                const code = jsQR(imageData.data, imageData.width, imageData.height, {
                    inversionAttempts: "dontInvert",
                });
                
                // Process QR code if found
                if (code) {
                    console.log("QR Code detected:", code.data);
                    
                    // Display QR code data
                    if (resultElement) {
                        resultElement.innerHTML = `
                            <div class="alert alert-success">
                                <h5><i class="bi bi-qr-code-scan"></i> QR Code Detected</h5>
                                <p><strong>Data:</strong> ${code.data}</p>
                                <button id="verifyScannedCode" class="btn btn-primary mt-2">Verify</button>
                            </div>
                        `;
                        
                        // Add event listener to verify button
                        document.getElementById('verifyScannedCode').addEventListener('click', function() {
                            verifyScannedCode(code.data);
                        });
                    }
                    
                    // Stop scanning
                    stopQRScanner();
                    return;
                }
            }
            
            // Continue scanning if no code found
            requestAnimationFrame(scan);
        };
        
        // Start scanning
        scan();
        
    } catch (error) {
        console.error('Error scanning QR code:', error);
        if (resultElement) {
            resultElement.innerHTML = `<div class="alert alert-danger">Error scanning QR code: ${error.message}</div>`;
        }
    }
}

async function importJsQR() {
    // Check if jsQR is already available
    if (window.jsQR) return window.jsQR;
    
    // Load jsQR library dynamically
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js';
        script.onload = () => resolve(window.jsQR);
        script.onerror = () => reject(new Error('Failed to load jsQR library'));
        document.head.appendChild(script);
    });
}

function verifyScannedCode(data) {
    const resultElement = document.getElementById('qrResult');
    
    // Determine if data is a ticket or standing zone
    let apiEndpoint, dataType;
    if (data.includes('|')) {
        const parts = data.split('|');
        if (parts.length === 4) {
            // Format is train_number|coach|seat_or_zone|phone
            if (parts[2].startsWith('S')) {
                apiEndpoint = '/api/verify-ticket';
                dataType = 'ticket_data';
            } else if (parts[2].startsWith('Z')) {
                apiEndpoint = '/api/verify-standing-zone';
                dataType = 'zone_data';
            }
        }
    }
    
    if (!apiEndpoint) {
        if (resultElement) {
            resultElement.innerHTML = `<div class="alert alert-danger">Invalid QR code format</div>`;
        }
        return;
    }
    
    // Send verification request
    fetch(apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [dataType]: data })
    })
    .then(response => response.json())
    .then(result => {
        if (resultElement) {
            if (result.status === 'success' && result.valid) {
                // Valid ticket or zone
                const details = result.ticket || result.zone;
                resultElement.innerHTML = `
                    <div class="alert alert-success">
                        <h5><i class="bi bi-check-circle"></i> Valid ${dataType === 'ticket_data' ? 'Ticket' : 'Standing Zone'}</h5>
                        <p><strong>Train:</strong> ${details.train_number}</p>
                        <p><strong>Coach:</strong> ${details.coach}</p>
                        <p><strong>${dataType === 'ticket_data' ? 'Seat' : 'Zone'}:</strong> ${dataType === 'ticket_data' ? details.seat : details.zone}</p>
                        <p><strong>Phone:</strong> ${details.phone}</p>
                        <p><strong>Created:</strong> ${details.created_at}</p>
                    </div>
                `;
            } else {
                // Invalid ticket or zone
                resultElement.innerHTML = `
                    <div class="alert alert-danger">
                        <h5><i class="bi bi-x-circle"></i> Invalid ${dataType === 'ticket_data' ? 'Ticket' : 'Standing Zone'}</h5>
                        <p>This QR code is not valid or has expired.</p>
                    </div>
                `;
            }
        }
    })
    .catch(error => {
        console.error('Error verifying QR code:', error);
        if (resultElement) {
            resultElement.innerHTML = `<div class="alert alert-danger">Error verifying QR code: ${error.message}</div>`;
        }
    });
}
