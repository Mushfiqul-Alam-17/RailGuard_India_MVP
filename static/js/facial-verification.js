let isCapturing = false;
let verificationMode = 'hash'; // Default to 'hash', will be updated if full face recognition is available

document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('startCamera');
    const captureBtn = document.getElementById('captureImage');
    const registerBtn = document.getElementById('registerFace');
    const verifyBtn = document.getElementById('verifyFace');
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const photoContainer = document.getElementById('photoContainer');
    const resultText = document.getElementById('resultText');
    const phoneInput = document.getElementById('phone');

    // Check if server has face recognition available
    fetch('/api/check-biometrics')
        .then(response => response.json())
        .then(data => {
            if (data.face_recognition_available) {
                verificationMode = 'face';
                console.log('Full facial recognition is available');
            } else {
                console.log('Using fallback hash-based verification');
            }
        })
        .catch(error => {
            console.error('Error checking biometrics capability:', error);
        });

    const socket = io();
    const cameraFeed = document.getElementById('camera-feed');
    const snapshot = document.getElementById('snapshot');
    const registerFaceBtn = document.getElementById('register-face');
    const verifyFaceBtn = document.getElementById('verify-face');
    const verificationResult = document.getElementById('verification-result');

    let stream = null;

    // Initialize camera
    async function initCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'user' },
                audio: false 
            });
            cameraFeed.srcObject = stream;
        } catch (err) {
            console.error('Error accessing camera:', err);
            alert('Unable to access camera. Please ensure camera permissions are granted.');
        }
    }

    // Take snapshot from camera
    function takeSnapshot() {
        const canvas = snapshot;
        const context = canvas.getContext('2d');

        // Set canvas dimensions to match video
        canvas.width = cameraFeed.videoWidth;
        canvas.height = cameraFeed.videoHeight;

        // Draw current video frame to canvas
        context.drawImage(cameraFeed, 0, 0, canvas.width, canvas.height);

        // Get image data as base64 string
        return canvas.toDataURL('image/jpeg');
    }

    // Register face
    registerFaceBtn.addEventListener('click', function() {
        console.log("Register Face button clicked"); // DEBUG
        const phone = phoneInput.value.trim();
        if (!phone) {
            alert('Please enter your phone number');
            return;
        }
        console.log("Phone number:", phone); // DEBUG

        const imageData = takeSnapshot();
        console.log("Snapshot taken for registration:", imageData.substring(0, 50) + "..."); // DEBUG (log start of data)

        fetch('/api/register-face', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, image_data: imageData })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showResult('Face registered successfully!', 'success');
            } else {
                showResult(data.message || 'Failed to register face', 'danger');
            }
        })
        .catch(err => {
            console.error('Error:', err);
            showResult('An error occurred', 'danger');
        });
    });

    // Verify face
    verifyFaceBtn.addEventListener('click', function() {
        console.log("Verify Face button clicked"); // DEBUG
        const phone = phoneInput.value.trim();
        if (!phone) {
            alert('Please enter your phone number');
            return;
        }
        console.log("Phone number:", phone); // DEBUG

        const imageData = takeSnapshot();
        console.log("Snapshot taken for verification:", imageData.substring(0, 50) + "..."); // DEBUG

        fetch('/api/verify-face', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, image_data: imageData })
        })
        .then(response => response.json())
        .then(data => {
            if (data.verified) {
                showResult('Face verification successful!', 'success');
            } else {
                showResult('Face verification failed', 'danger');
            }
        })
        .catch(err => {
            console.error('Error:', err);
            showResult('An error occurred', 'danger');
        });
    });

    // Display result message
    function showResult(message, type) {
        verificationResult.innerText = message;
        verificationResult.className = `mt-3 alert alert-${type}`;
        verificationResult.style.display = 'block';

        // Hide after 5 seconds
        setTimeout(() => {
            verificationResult.style.display = 'none';
        }, 5000);
    }

    // Listen for real-time verification results
    socket.on('face_verification_result', function(data) {
        if (data.phone === phoneInput.value.trim()) {
            showResult(data.verified ? 
                'Face verification successful!' : 
                'Face verification failed', 
                data.verified ? 'success' : 'danger');
        }
    });

    // Initialize camera when page loads
    initCamera();

    // Clean up on page unload
    window.addEventListener('beforeunload', function() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });
});