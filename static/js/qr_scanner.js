// QR Code Scanner functionality for RailGuard India - Simplified Direct Implementation

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements for scan buttons
    const scanQRTicketBtn = document.getElementById('scanQRTicketBtn');
    const scanQRZoneBtn = document.getElementById('scanQRZoneBtn');
    
    // Attach click events to scan buttons - directly use the simulate function
    if (scanQRTicketBtn) {
        scanQRTicketBtn.addEventListener('click', function() {
            simulateScan('ticket');
        });
    }
    
    if (scanQRZoneBtn) {
        scanQRZoneBtn.addEventListener('click', function() {
            simulateScan('zone');
        });
    }
});

// Simulate QR scan for demo purposes
function simulateScan(dataType, sampleData) {
    // Demo data
    const demoTicketData = 'T12345-C04-S23';
    const demoZoneData = 'Z12345-C02-Z03';
    
    // Get input element
    const targetInput = document.getElementById(dataType === 'ticket' ? 'ticketData' : 'zoneData');
    
    if (targetInput) {
        // Set value with provided sample data or default demo data
        targetInput.value = sampleData || (dataType === 'ticket' ? demoTicketData : demoZoneData);
        
        // Trigger verification button
        const verifyBtn = document.getElementById(dataType === 'ticket' ? 'verifyTicketBtn' : 'verifyZoneBtn');
        if (verifyBtn) {
            verifyBtn.click();
        }
    }
}
