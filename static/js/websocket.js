
// WebSocket connection for real-time updates
let socket;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

document.addEventListener('DOMContentLoaded', function() {
    initializeSocketConnection();
});

function initializeSocketConnection() {
    try {
        // Connect to WebSocket server
        socket = io();
        
        // Connection events
        socket.on('connect', handleSocketConnect);
        socket.on('disconnect', handleSocketDisconnect);
        socket.on('connect_error', handleSocketError);
        
        // Application-specific events
        setupApplicationEvents();
        
        console.log('WebSocket: Initialization complete');
    } catch (error) {
        console.error('WebSocket: Initialization failed', error);
    }
}

function handleSocketConnect() {
    console.log('WebSocket: Connected to server');
    reconnectAttempts = 0;
    
    // Show connected status if indicator exists
    const statusIndicator = document.getElementById('connectionStatus');
    if (statusIndicator) {
        statusIndicator.className = 'badge bg-success';
        statusIndicator.textContent = 'Connected';
    }
}

function handleSocketDisconnect() {
    console.log('WebSocket: Disconnected from server');
    
    // Show disconnected status if indicator exists
    const statusIndicator = document.getElementById('connectionStatus');
    if (statusIndicator) {
        statusIndicator.className = 'badge bg-danger';
        statusIndicator.textContent = 'Disconnected';
    }
    
    // Try to reconnect if under attempt limit
    if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        console.log(`WebSocket: Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`);
        setTimeout(initializeSocketConnection, 3000);
    }
}

function handleSocketError(error) {
    console.error('WebSocket: Connection error', error);
}

function setupApplicationEvents() {
    // Listen for trust ID updates
    socket.on('trust_id_update', function(data) {
        console.log('Trust ID update received:', data);
        updateTrustIDStatus(data);
    });
    
    // Listen for face verification results
    socket.on('face_verification_result', function(data) {
        console.log('Face verification result received:', data);
        updateVerificationStatus(data);
    });
    
    // Listen for seat updates
    socket.on('seat_update', function(data) {
        console.log('Seat update received:', data);
        updateSeatStatus(data);
    });
    
    // Listen for complaint updates
    socket.on('complaint_update', function(data) {
        console.log('Complaint update received:', data);
        updateComplaintStatus(data);
    });
}

// Update trust ID status in UI
function updateTrustIDStatus(data) {
    const trustIdElements = document.querySelectorAll(`.trust-id-status[data-phone="${data.phone}"]`);
    if (trustIdElements.length > 0) {
        trustIdElements.forEach(element => {
            if (data.has_face) {
                element.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i> Face Registered';
            } else {
                element.innerHTML = '<i class="bi bi-x-circle-fill text-danger"></i> No Face Registered';
            }
        });
    }
}

// Update face verification status in UI
function updateVerificationStatus(data) {
    const verificationResult = document.getElementById('verification-result');
    if (verificationResult && document.getElementById('phone').value === data.phone) {
        if (data.verified) {
            verificationResult.innerText = 'Face verification successful!';
            verificationResult.className = 'mt-3 alert alert-success';
        } else {
            verificationResult.innerText = 'Face verification failed';
            verificationResult.className = 'mt-3 alert alert-danger';
        }
        verificationResult.style.display = 'block';
        
        // Hide after 5 seconds
        setTimeout(() => {
            verificationResult.style.display = 'none';
        }, 5000);
    }
}

// Update seat status in UI
function updateSeatStatus(data) {
    const seatElement = document.querySelector(`.seat[data-coach="${data.coach}"][data-seat="${data.seat}"]`);
    if (seatElement) {
        // Update CSS classes based on status
        seatElement.className = `seat seat-${data.status}`;
        
        // Update data attribute
        seatElement.setAttribute('data-status', data.status);
        
        // If there's an occupant, update that too
        if (data.phone) {
            seatElement.setAttribute('data-phone', data.phone);
        } else {
            seatElement.removeAttribute('data-phone');
        }
    }
}

// Update complaint status in UI
function updateComplaintStatus(data) {
    // This could update a complaints table or notification area
    const complaintsTable = document.getElementById('complaints-table');
    if (complaintsTable && data.id) {
        // Check if complaint already exists in table
        const existingRow = document.querySelector(`tr[data-complaint-id="${data.id}"]`);
        
        if (!existingRow) {
            // Add new complaint to table
            const newRow = document.createElement('tr');
            newRow.setAttribute('data-complaint-id', data.id);
            
            newRow.innerHTML = `
                <td>${data.id}</td>
                <td>${data.phone}</td>
                <td>${data.message}</td>
                <td><span class="badge bg-${data.risk_level === 'High' ? 'danger' : (data.risk_level === 'Medium' ? 'warning' : 'success')}">${data.risk_level}</span></td>
                <td>${new Date(data.timestamp).toLocaleString()}</td>
            `;
            
            complaintsTable.querySelector('tbody').prepend(newRow);
        }
    }
}xists
    const statusIndicator = document.getElementById('socketStatus');
    if (statusIndicator) {
        statusIndicator.className = 'socket-status connected';
        statusIndicator.setAttribute('title', 'Connected to server');
    }
    
    // Request initial data if needed
    // socket.emit('request_initial_data');
}

function handleSocketDisconnect() {
    console.log('WebSocket: Disconnected from server');
    
    // Show disconnected status if indicator exists
    const statusIndicator = document.getElementById('socketStatus');
    if (statusIndicator) {
        statusIndicator.className = 'socket-status disconnected';
        statusIndicator.setAttribute('title', 'Disconnected from server');
    }
    
    // Attempt to reconnect
    if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        console.log(`WebSocket: Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`);
        
        // Add reconnect logic if socket.io automatic reconnect is not sufficient
    }
}

function handleSocketError(error) {
    console.error('WebSocket: Connection error', error);
}

function setupApplicationEvents() {
    // Seat management updates
    socket.on('seat_update', (data) => {
        updateSeatStatus(data.coach, data.seat, data.status);
    });
    
    // Complaint updates
    socket.on('complaint_update', (data) => {
        addNewComplaint(data);
    });
    
    // Trust ID updates
    socket.on('trust_id_update', (data) => {
        updateTrustIDStatus(data);
    });
    
    // Face verification results
    socket.on('face_verification_result', (data) => {
        handleFaceVerificationResult(data);
    });
    
    // Standing zone updates
    socket.on('standing_zone_update', (data) => {
        updateStandingZoneStatus(data);
    });
    
    // Emergency alerts
    socket.on('emergency_alert', (data) => {
        showEmergencyAlert(data);
    });
}

// Handler functions for WebSocket events
function updateSeatStatus(coach, seat, status) {
    const seatElement = document.querySelector(`[data-coach="${coach}"][data-seat="${seat}"]`);
    if (seatElement) {
        // Remove all status classes
        seatElement.classList.remove('vacant', 'occupied', 'disputed');
        
        // Add new status class
        seatElement.classList.add(status);
        seatElement.setAttribute('data-status', status);
        
        // Update heatmap if applicable
        if (typeof updateHeatmap === 'function') {
            updateHeatmap();
        }
        
        // Show notification
        showNotification(`Seat ${seat} in coach ${coach} is now ${status}`);
    }
}

function addNewComplaint(data) {
    const complaintsList = document.getElementById('complaintsList');
    if (complaintsList) {
        // Create new complaint element
        const newComplaint = document.createElement('div');
        newComplaint.className = `complaint-item ${data.risk_level.toLowerCase()}`;
        
        newComplaint.innerHTML = `
            <div class="complaint-header">
                <span class="complaint-id">#${data.id}</span>
                <span class="complaint-time">${formatTimeAgo(data.timestamp)}</span>
            </div>
            <div class="complaint-message">${data.message}</div>
            <div class="complaint-footer">
                <span class="complaint-phone">${maskPhone(data.phone)}</span>
                <span class="badge bg-${getRiskBadgeColor(data.risk_level)}">${data.risk_level}</span>
            </div>
        `;
        
        // Add to list
        complaintsList.prepend(newComplaint);
        
        // Show notification for high risk complaints
        if (data.risk_level.toLowerCase() === 'high') {
            showNotification(`New high risk complaint: ${data.message.substring(0, 30)}...`, 'warning');
        }
    }
    
    // Update complaint count if exists
    const countElement = document.getElementById('complaintCount');
    if (countElement) {
        const currentCount = parseInt(countElement.textContent, 10);
        countElement.textContent = currentCount + 1;
    }
}

function updateTrustIDStatus(data) {
    // Update Trust ID list if on that page
    const trustIdList = document.getElementById('trustIdList');
    if (trustIdList && data.id) {
        // Check if the Trust ID is already in the list
        const existingItem = document.querySelector(`[data-trust-id="${data.id}"]`);
        if (existingItem) {
            // Update existing item
            if (data.has_face) {
                existingItem.querySelector('.face-status').innerHTML = 
                    '<span class="badge bg-success">Face Registered</span>';
            }
        } else {
            // Add new item
            const newItem = document.createElement('tr');
            newItem.setAttribute('data-trust-id', data.id);
            
            newItem.innerHTML = `
                <td>${maskPhone(data.phone)}</td>
                <td>${data.id.substring(0, 8)}...</td>
                <td>${formatDate(data.created_at)}</td>
                <td class="face-status">
                    ${data.has_face ? 
                        '<span class="badge bg-success">Face Registered</span>' : 
                        '<span class="badge bg-secondary">No Face</span>'}
                </td>
            `;
            
            trustIdList.appendChild(newItem);
        }
    }
}

function handleFaceVerificationResult(data) {
    const resultContainer = document.getElementById('faceVerificationResult');
    if (resultContainer) {
        if (data.verified) {
            resultContainer.innerHTML = `
                <div class="alert alert-success">
                    <h5><i class="bi bi-check-circle"></i> Verification Successful</h5>
                    <p>Your face has been verified successfully.</p>
                </div>
            `;
        } else {
            resultContainer.innerHTML = `
                <div class="alert alert-danger">
                    <h5><i class="bi bi-x-circle"></i> Verification Failed</h5>
                    <p>Face verification failed. Please try again or contact support.</p>
                </div>
            `;
        }
    }
    
    // Also show a notification
    if (data.verified) {
        showNotification('Face verification successful!', 'success');
    } else {
        showNotification('Face verification failed', 'danger');
    }
}

function updateStandingZoneStatus(data) {
    const zoneElement = document.querySelector(`[data-zone="${data.zone}"][data-coach="${data.coach}"]`);
    if (zoneElement) {
        // Update zone status
        zoneElement.setAttribute('data-status', data.status);
        
        // Update capacity display
        const capacityElement = zoneElement.querySelector('.zone-capacity');
        if (capacityElement) {
            capacityElement.textContent = `${data.allocated}/${data.capacity}`;
        }
        
        // Update status indicator
        const statusElement = zoneElement.querySelector('.zone-indicator');
        if (statusElement) {
            statusElement.className = 'zone-indicator';
            if (data.allocated >= data.capacity) {
                statusElement.classList.add('zone-red');
            } else if (data.allocated >= data.capacity * 0.7) {
                statusElement.classList.add('zone-yellow');
            } else {
                statusElement.classList.add('zone-green');
            }
        }
    }
}

function showEmergencyAlert(data) {
    // Create emergency alert
    const alertElement = document.createElement('div');
    alertElement.className = 'emergency-alert';
    
    alertElement.innerHTML = `
        <div class="alert alert-danger emergency-alert-box">
            <h4><i class="bi bi-exclamation-triangle-fill"></i> Emergency Alert</h4>
            <p>${data.message}</p>
            <div class="emergency-details">
                <strong>Location:</strong> ${data.location}<br>
                <strong>Time:</strong> ${formatDate(data.timestamp)}<br>
                ${data.contact ? `<strong>Contact:</strong> ${maskPhone(data.contact)}` : ''}
            </div>
            <button class="btn btn-sm btn-danger mt-2 acknowledge-btn">Acknowledge</button>
        </div>
    `;
    
    // Add to document
    document.body.appendChild(alertElement);
    
    // Add close handler
    const closeBtn = alertElement.querySelector('.acknowledge-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            alertElement.remove();
            
            // Notify server of acknowledgment
            socket.emit('emergency_acknowledged', { id: data.id });
        });
    }
    
    // Auto-remove after 30 seconds if not acknowledged
    setTimeout(() => {
        if (document.body.contains(alertElement)) {
            alertElement.remove();
        }
    }, 30000);
}

// Helper functions
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `toast toast-${type}`;
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', 'assertive');
    notification.setAttribute('aria-atomic', 'true');
    
    notification.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">RailGuard Alert</strong>
            <small>${formatTime(new Date())}</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">${message}</div>
    `;
    
    // Add to notifications container or create one
    let notificationsContainer = document.getElementById('notifications');
    if (!notificationsContainer) {
        notificationsContainer = document.createElement('div');
        notificationsContainer.id = 'notifications';
        notificationsContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(notificationsContainer);
    }
    
    notificationsContainer.appendChild(notification);
    
    // Initialize toast
    const toast = new bootstrap.Toast(notification, { delay: 5000 });
    toast.show();
    
    // Auto-remove after hiding
    notification.addEventListener('hidden.bs.toast', function() {
        notification.remove();
    });
}

function formatTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffDay > 0) {
        return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
    } else if (diffHour > 0) {
        return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
    } else if (diffMin > 0) {
        return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
    } else {
        return 'Just now';
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function maskPhone(phone) {
    if (phone.length < 4) return phone;
    return phone.substring(0, phone.length - 4).replace(/./g, '*') + phone.substring(phone.length - 4);
}

function getRiskBadgeColor(riskLevel) {
    switch (riskLevel.toLowerCase()) {
        case 'high':
            return 'danger';
        case 'medium':
            return 'warning';
        default:
            return 'success';
    }
}
