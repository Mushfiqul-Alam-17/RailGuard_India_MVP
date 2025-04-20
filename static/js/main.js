// RailGuard India - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Dashboard chart initialization
    initializeCharts();

    // Handle seat management interactions
    setupSeatManagement();

    // Setup complaint risk level indicators
    setupRiskIndicators();

    // Setup QR code verification
    setupQRVerification();
});

// Initialize dashboard charts
function initializeCharts() {
    // Check if charts elements exist
    const complaintsChartEl = document.getElementById('complaintsChart');
    const ticketsChartEl = document.getElementById('ticketsChart');
    
    if (complaintsChartEl && ticketsChartEl) {
        // Complaints chart
        const complaintsCtx = complaintsChartEl.getContext('2d');
        new Chart(complaintsCtx, {
            type: 'pie',
            data: {
                labels: ['Low Risk', 'Medium Risk', 'High Risk'],
                datasets: [{
                    data: [25, 15, 10],
                    backgroundColor: ['#28a745', '#ffc107', '#dc3545']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
        
        // Tickets chart
        const ticketsCtx = ticketsChartEl.getContext('2d');
        new Chart(ticketsCtx, {
            type: 'bar',
            data: {
                labels: ['S1', 'S2', 'S3', 'S4', 'S5'],
                datasets: [{
                    label: 'Tickets Issued',
                    data: [68, 65, 60, 45, 55],
                    backgroundColor: '#0d6efd'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
}

// Seat Heatmap functionality
function setupSeatManagement() {
    const coachSelector = document.getElementById('coachSelector');
    if (coachSelector) {
        coachSelector.addEventListener('change', function() {
            updateSeatMap(this.value);
        });
        
        // Initial update
        updateSeatMap(coachSelector.value);
    }
    
    // Update heatmap initially
    updateHeatmap();
}

function updateSeatMap(coach) {
    const seatMap = document.getElementById('seatMap');
    if (!seatMap) return;
    
    // Clear existing map
    seatMap.innerHTML = '';
    
    // Generate seat layout (simplified for demo)
    const rowCount = 12;
    const seatsPerRow = 6;
    
    for (let row = 1; row <= rowCount; row++) {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'seat-row';
        
        for (let seat = 1; seat <= seatsPerRow; seat++) {
            const seatNumber = (row - 1) * seatsPerRow + seat;
            const seatDiv = document.createElement('div');
            seatDiv.className = 'seat';
            
            // Randomly assign status for demo
            const statuses = ['vacant', 'occupied', 'disputed'];
            const randomStatus = statuses[Math.floor(Math.random() * 3)];
            seatDiv.classList.add(randomStatus);
            
            seatDiv.setAttribute('data-coach', coach);
            seatDiv.setAttribute('data-seat', seatNumber);
            seatDiv.setAttribute('data-status', randomStatus);
            
            seatDiv.textContent = seatNumber;
            
            // Add heat overlay
            const heatOverlay = document.createElement('div');
            heatOverlay.className = 'heat-overlay';
            seatDiv.appendChild(heatOverlay);
            
            // Add click handler
            seatDiv.addEventListener('click', function() {
                selectSeat(this);
            });
            
            rowDiv.appendChild(seatDiv);
        }
        
        seatMap.appendChild(rowDiv);
    }
    
    updateHeatmap();
}

function selectSeat(seatElement) {
    // Highlight selected seat
    const allSeats = document.querySelectorAll('.seat');
    allSeats.forEach(seat => seat.classList.remove('selected'));
    seatElement.classList.add('selected');
    
    // Update info panel
    const seatInfo = document.getElementById('seatInfo');
    if (seatInfo) {
        const coach = seatElement.getAttribute('data-coach');
        const seat = seatElement.getAttribute('data-seat');
        const status = seatElement.getAttribute('data-status');
        
        // Update form if it exists
        const coachInput = document.getElementById('coachInput');
        const seatInput = document.getElementById('seatInput');
        const statusSelect = document.getElementById('statusSelect');
        
        if (coachInput) coachInput.value = coach;
        if (seatInput) seatInput.value = seat;
        if (statusSelect) statusSelect.value = status;
    }
}

function calculateOccupancyRate(seatElement) {
    // In a real application, this would be based on actual data
    // For now, we'll use seat number as a proxy for demo
    const seatNumber = parseInt(seatElement.getAttribute('data-seat'), 10);
    const totalSeats = 72; // Typical seats in a coach
    
    // Higher seat number = higher position in coach = higher heat
    return seatNumber / totalSeats;
}

function updateHeatmapColor(seatElement, occupancyRate) {
    const heatOverlay = seatElement.querySelector('.heat-overlay');
    if (!heatOverlay) return;
    
    // Remove existing heat classes
    heatOverlay.classList.remove('heat-high', 'heat-medium', 'heat-low');
    
    // Apply heat based on occupancy rate
    if (occupancyRate > 0.7) {
        heatOverlay.classList.add('heat-high');
    } else if (occupancyRate > 0.3) {
        heatOverlay.classList.add('heat-medium');
    } else {
        heatOverlay.classList.add('heat-low');
    }
}

// Update heatmap colors based on occupancy
function updateHeatmap() {
    const seats = document.querySelectorAll('.seat');
    seats.forEach(seat => {
        const occupancyRate = calculateOccupancyRate(seat);
        updateHeatmapColor(seat, occupancyRate);
    });
}

// Setup risk indicators for complaints
function setupRiskIndicators() {
    const riskElements = document.querySelectorAll('.risk-indicator');
    riskElements.forEach(element => {
        const riskLevel = element.getAttribute('data-risk');
        if (riskLevel === 'high') {
            element.classList.add('risk-high');
        } else if (riskLevel === 'medium') {
            element.classList.add('risk-medium');
        } else {
            element.classList.add('risk-low');
        }
    });
}
function initializeCharts() {
    const complaintsChartEl = document.getElementById('complaintsChart');
    if (complaintsChartEl) {
        const ctx = complaintsChartEl.getContext('2d');
        
        // Sample data - In production, this would come from an API
        const data = {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'High Risk Complaints',
                data: [12, 19, 3, 5, 2, 3],
                backgroundColor: '#dc3545',
                borderColor: '#dc3545'
            }, {
                label: 'Low Risk Complaints',
                data: [5, 10, 15, 7, 8, 12],
                backgroundColor: '#198754',
                borderColor: '#198754'
            }]
        };
        
        new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Monthly Complaints'
                    }
                }
            }
        });
    }

    const ticketsChartEl = document.getElementById('ticketsChart');
    if (ticketsChartEl) {
        const ctx = ticketsChartEl.getContext('2d');
        
        // Sample data
        const data = {
            labels: ['Regular Tickets', 'Standing Zone', 'Emergency Slips'],
            datasets: [{
                data: [65, 25, 10],
                backgroundColor: ['#0d6efd', '#0dcaf0', '#ffc107']
            }]
        };
        
        new Chart(ctx, {
            type: 'doughnut',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    title: {
                        display: true,
                        text: 'Ticket Distribution'
                    }
                }
            }
        });
    }
}

// Setup seat management interactions
function setupSeatManagement() {
    const seatMap = document.querySelector('.seat-map');
    
    if (seatMap) {
        // Add event listeners to seats
        const seats = seatMap.querySelectorAll('.seat');
        
        seats.forEach(seat => {
            seat.addEventListener('click', function() {
                // Toggle selected state
                seat.classList.toggle('selected');
                
                // Update form if it exists
                const seatInput = document.getElementById('seat_number');
                const coachInput = document.getElementById('coach');
                const statusInput = document.getElementById('status');
                
                if (seatInput && coachInput && statusInput) {
                    if (seat.classList.contains('selected')) {
                        seatInput.value = seat.dataset.seat;
                        coachInput.value = seat.dataset.coach;
                        statusInput.value = seat.classList.contains('occupied') ? 'vacant' : 'occupied';
                    } else {
                        seatInput.value = '';
                        statusInput.value = '';
                    }
                }
            });
        });
    }
}

// Setup complaint risk level indicators
function setupRiskIndicators() {
    const complaintItems = document.querySelectorAll('.complaint-item');
    
    if (complaintItems.length > 0) {
        complaintItems.forEach(item => {
            const riskLevel = item.dataset.risk;
            const indicator = item.querySelector('.risk-indicator');
            
            if (indicator) {
                if (riskLevel === 'High') {
                    indicator.classList.add('risk-high');
                    indicator.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i> High Risk';
                } else {
                    indicator.classList.add('risk-low');
                    indicator.innerHTML = '<i class="bi bi-check-circle-fill"></i> Low Risk';
                }
            }
        });
    }
}

// Setup QR code verification
function setupQRVerification() {
    const verifyTicketBtn = document.getElementById('verifyTicketBtn');
    const verifyZoneBtn = document.getElementById('verifyZoneBtn');
    
    if (verifyTicketBtn) {
        verifyTicketBtn.addEventListener('click', function() {
            const ticketData = document.getElementById('ticketData').value;
            
            if (!ticketData) {
                showAlert('Please scan or enter ticket data', 'danger');
                return;
            }
            
            // Send verification request
            fetch('/api/verify-ticket', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ticket_data: ticketData })
            })
            .then(response => response.json())
            .then(data => {
                if (data.valid) {
                    showTicketDetails(data.ticket);
                    showAlert('Valid ticket', 'success');
                } else {
                    showAlert('Invalid ticket', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Error verifying ticket', 'danger');
            });
        });
    }
    
    if (verifyZoneBtn) {
        verifyZoneBtn.addEventListener('click', function() {
            const zoneData = document.getElementById('zoneData').value;
            
            if (!zoneData) {
                showAlert('Please scan or enter zone data', 'danger');
                return;
            }
            
            // Send verification request
            fetch('/api/verify-standing-zone', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ zone_data: zoneData })
            })
            .then(response => response.json())
            .then(data => {
                if (data.valid) {
                    showZoneDetails(data.zone);
                    showAlert('Valid standing zone allocation', 'success');
                } else {
                    showAlert('Invalid standing zone allocation', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Error verifying standing zone', 'danger');
            });
        });
    }
}

// Helper function to show alerts
function showAlert(message, type) {
    const alertContainer = document.getElementById('alertContainer');
    
    if (alertContainer) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.role = 'alert';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    }
}

// Universal Modal Dismiss System
// This adds a global click handler for dismissing any modal
document.addEventListener('DOMContentLoaded', function() {
    // Add keyboard shortcut (Escape key) for closing modals
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            dismissAllModals();
        }
    });
    
    // Once the DOM is loaded, enhance all modals with dismiss buttons
    setTimeout(enhanceAllModals, 500);
    
    // Add observer to catch dynamically added modals
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                // Check if new modals were added
                setTimeout(enhanceAllModals, 100);
            }
        });
    });
    
    // Start observing the document body for modals
    observer.observe(document.body, { childList: true, subtree: true });
});

// Function to dismiss all open modals
function dismissAllModals() {
    // Find all open modals and close them
    const openModals = document.querySelectorAll('.modal.show');
    openModals.forEach(modalElement => {
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        if (modalInstance) {
            modalInstance.hide();
        } else {
            // Fallback if instance not available
            modalElement.classList.remove('show');
            modalElement.style.display = 'none';
            document.body.classList.remove('modal-open');
            const modalBackdrops = document.querySelectorAll('.modal-backdrop');
            modalBackdrops.forEach(backdrop => backdrop.remove());
        }
    });
}

// Function to enhance all modals with dismiss button
function enhanceAllModals() {
    // Target all modals in the application
    const allModals = document.querySelectorAll('.modal');
    
    allModals.forEach(modalElement => {
        // Check if we've already enhanced this modal
        if (!modalElement.classList.contains('enhanced-with-dismiss')) {
            modalElement.classList.add('enhanced-with-dismiss');
            
            // Create dismiss button
            const dismissButton = document.createElement('button');
            dismissButton.classList.add('modal-dismiss-btn');
            dismissButton.innerHTML = '×';
            dismissButton.title = 'Dismiss All Popups';
            dismissButton.setAttribute('type', 'button');
            
            // Style the dismiss button
            dismissButton.style.position = 'absolute';
            dismissButton.style.top = '10px';
            dismissButton.style.right = '10px';
            dismissButton.style.zIndex = '1060';
            dismissButton.style.backgroundColor = '#ff3b30';
            dismissButton.style.color = 'white';
            dismissButton.style.border = 'none';
            dismissButton.style.borderRadius = '50%';
            dismissButton.style.width = '32px';
            dismissButton.style.height = '32px';
            dismissButton.style.fontSize = '20px';
            dismissButton.style.lineHeight = '1';
            dismissButton.style.cursor = 'pointer';
            dismissButton.style.boxShadow = '0 2px 5px rgba(0,0,0,0.3)';
            
            // Add hover effect
            dismissButton.addEventListener('mouseover', function() {
                this.style.backgroundColor = '#ff1a1a';
            });
            
            dismissButton.addEventListener('mouseout', function() {
                this.style.backgroundColor = '#ff3b30';
            });
            
            // Add click handler to dismiss all modals
            dismissButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                dismissAllModals();
            });
            
            // Add button to modal
            modalElement.appendChild(dismissButton);
        }
    });
}

// Helper function to show ticket details
function showTicketDetails(ticket) {
    const detailsContainer = document.getElementById('ticketDetailsContainer');
    
    if (detailsContainer) {
        detailsContainer.innerHTML = `
            <div class="ticket-details mt-3">
                <h5 class="ticket-title">Ticket Details</h5>
                <div class="ticket-info-item">
                    <span class="ticket-info-label">Train:</span>
                    <span class="ticket-info-value">${ticket.train_number}</span>
                </div>
                <div class="ticket-info-item">
                    <span class="ticket-info-label">Coach:</span>
                    <span class="ticket-info-value">${ticket.coach}</span>
                </div>
                <div class="ticket-info-item">
                    <span class="ticket-info-label">Seat:</span>
                    <span class="ticket-info-value">${ticket.seat}</span>
                </div>
                <div class="ticket-info-item">
                    <span class="ticket-info-label">Phone:</span>
                    <span class="ticket-info-value">${ticket.phone}</span>
                </div>
                <div class="ticket-info-item">
                    <span class="ticket-info-label">Created:</span>
                    <span class="ticket-info-value">${ticket.created_at}</span>
                </div>
            </div>
        `;
    }
}

// Helper function to show zone details
function showZoneDetails(zone) {
    const detailsContainer = document.getElementById('zoneDetailsContainer');
    
    if (detailsContainer) {
        detailsContainer.innerHTML = `
            <div class="ticket-details mt-3">
                <h5 class="ticket-title">Standing Zone Details</h5>
                <div class="ticket-info-item">
                    <span class="ticket-info-label">Train:</span>
                    <span class="ticket-info-value">${zone.train_number}</span>
                </div>
                <div class="ticket-info-item">
                    <span class="ticket-info-label">Coach:</span>
                    <span class="ticket-info-value">${zone.coach}</span>
                </div>
                <div class="ticket-info-item">
                    <span class="ticket-info-label">Zone:</span>
                    <span class="ticket-info-value">${zone.zone}</span>
                </div>
                <div class="ticket-info-item">
                    <span class="ticket-info-label">Phone:</span>
                    <span class="ticket-info-value">${zone.phone}</span>
                </div>
                <div class="ticket-info-item">
                    <span class="ticket-info-label">Created:</span>
                    <span class="ticket-info-value">${zone.created_at}</span>
                </div>
            </div>
        `;
    }
}

// Function to submit a complaint via API
function submitComplaintAPI(phone, message) {
    if (!phone || !message) {
        showAlert('Phone number and message are required', 'danger');
        return;
    }
    
    fetch('/api/submit-complaint', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ phone, message })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' || data.status === 'warning') {
            showAlert(data.message, data.status === 'success' ? 'success' : 'warning');
            
            // Update UI with new complaint
            const complaintsContainer = document.getElementById('complaintsContainer');
            if (complaintsContainer) {
                const newComplaint = document.createElement('div');
                newComplaint.className = 'complaint-item p-3 mb-3 border rounded';
                newComplaint.dataset.risk = data.risk_level;
                
                newComplaint.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong>Phone:</strong> ${maskPhone(phone)}<br>
                            <strong>Message:</strong> ${message}<br>
                            <small class="text-muted">Just now</small>
                        </div>
                        <div class="risk-indicator ${data.risk_level === 'High' ? 'risk-high' : 'risk-low'}">
                            <i class="bi ${data.risk_level === 'High' ? 'bi-exclamation-triangle-fill' : 'bi-check-circle-fill'}"></i> 
                            ${data.risk_level} Risk
                        </div>
                    </div>
                `;
                
                complaintsContainer.prepend(newComplaint);
            }
            
            // Reset form
            document.getElementById('complaintForm').reset();
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error submitting complaint', 'danger');
    });
}

// Helper function to mask phone number
function maskPhone(phone) {
    return phone.toString().slice(0, -4).replace(/./g, '*') + phone.slice(-4);
}
