let socket = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const baseReconnectDelay = 1000; // 1 second initial delay
let heartbeatInterval;

// Initialize WebSocket connection when page loads
document.addEventListener('DOMContentLoaded', () => {
    connect();
});

function connect() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        return;
    }

    socket = new WebSocket(`wss://${window.location.host}/ws/shipment-updates/`);

    // Heartbeat to maintain connection
    heartbeatInterval = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'heartbeat',
                timestamp: Date.now()
            }));
        }
    }, 30000); // 30 seconds

    socket.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttempts = 0;
        // Request initial data on connection
        socket.send(JSON.stringify({
            action: 'get_initial_data',
            timestamp: Date.now()
        }));
    };

    socket.onclose = (event) => {
        console.log(`WebSocket disconnected: ${event.reason}`);
        clearInterval(heartbeatInterval);
        
        if (reconnectAttempts < maxReconnectAttempts) {
            const delay = Math.min(
                baseReconnectDelay * Math.pow(2, reconnectAttempts),
                30000 // Max 30 seconds delay
            );
            console.log(`Reconnecting attempt ${reconnectAttempts + 1} in ${delay}ms...`);
            setTimeout(connect, delay);
            reconnectAttempts++;
        } else {
            console.error('Max reconnection attempts reached');
            showConnectionError('Failed to connect to real-time updates. Please refresh the page.');
        }
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    socket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        console.log('WebSocket message received:', data);
        
        switch(data.type) {
            case 'shipment.update':
                updateShipment(data.payload);
                break;
            case 'sensor.data':
                updateSensorData(data.payload);
                break;
            case 'alert.triggered':
                showAlert(data.payload);
                break;
        }
    };
}

// Update shipment in the table
function updateShipment(shipment) {
    const row = document.querySelector(`#shipment-${shipment.tracking_id}`);
    
    if (row) {
        // Update existing row
        row.querySelector('.shipment-status').textContent = shipment.status;
        row.querySelector('.shipment-location').textContent = shipment.current_location || 'N/A';
        row.querySelector('.shipment-updated').textContent = new Date(shipment.updated_at).toLocaleString();
    } else {
        // Add new row
        const tbody = document.getElementById('shipments-table');
        const newRow = document.createElement('tr');
        newRow.id = `shipment-${shipment.tracking_id}`;
        newRow.className = 'hover:bg-gray-50';
        newRow.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                ${shipment.tracking_id}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${shipment.product_name}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                    ${getStatusColor(shipment.status)}">
                    ${shipment.status}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 shipment-location">
                ${shipment.current_location || 'N/A'}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 shipment-updated">
                ${new Date(shipment.updated_at).toLocaleString()}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <a href="/shipments/${shipment.tracking_id}/" class="text-blue-600 hover:text-blue-900">View</a>
            </td>
        `;
        tbody.prepend(newRow);
    }
    
    updateStats();
}

// Update sensor data on the map
function updateSensorData(sensorData) {
    const marker = getOrCreateMarker(sensorData.shipment_id);
    marker.setLatLng([sensorData.latitude, sensorData.longitude]);
    marker.bindPopup(`
        <b>Shipment #${sensorData.shipment_id}</b><br>
        Status: ${sensorData.status}<br>
        Temp: ${sensorData.temperature}°C<br>
        Humidity: ${sensorData.humidity}%<br>
        ${sensorData.tamper_status ? '<span class="text-red-500">TAMPER DETECTED</span>' : ''}
    `);
    
    updateStats();
}

// Show alert notification
function showAlert(alert) {
    const alertsList = document.getElementById('alerts-list');
    const alertElement = document.createElement('div');
    alertElement.className = `p-3 border-l-4 ${getAlertBorderColor(alert.severity)} bg-${getAlertBgColor(alert.severity)}`;
    alertElement.innerHTML = `
        <div class="flex justify-between">
            <p class="text-sm font-medium ${getAlertTextColor(alert.severity)}">${alert.message}</p>
            <span class="text-xs ${getAlertTextColor(alert.severity)}">Just now</span>
        </div>
        <p class="text-xs ${getAlertTextColor(alert.severity)} mt-1">Shipment #${alert.shipment_id}</p>
    `;
    alertsList.prepend(alertElement);
    
    // Show toast notification
    showToast(alert.message, alert.severity);
    
    updateStats();
}

// Helper functions
function getStatusColor(status) {
    const colors = {
        'CREATED': 'bg-blue-100 text-blue-800',
        'IN_TRANSIT': 'bg-yellow-100 text-yellow-800',
        'DELIVERED': 'bg-green-100 text-green-800',
        'HELD': 'bg-purple-100 text-purple-800',
        'TAMPERED': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
}

function getAlertBorderColor(severity) {
    return {
        'LOW': 'border-blue-500',
        'MEDIUM': 'border-yellow-500',
        'HIGH': 'border-orange-500',
        'CRITICAL': 'border-red-500'
    }[severity] || 'border-gray-500';
}

function getAlertBgColor(severity) {
    return {
        'LOW': 'blue-50',
        'MEDIUM': 'yellow-50',
        'HIGH': 'orange-50',
        'CRITICAL': 'red-50'
    }[severity] || 'gray-50';
}

function getAlertTextColor(severity) {
    return {
        'LOW': 'text-blue-800',
        'MEDIUM': 'text-yellow-800',
        'HIGH': 'text-orange-800',
        'CRITICAL': 'text-red-800'
    }[severity] || 'text-gray-800';
}

function showToast(message, severity) {
    // Implementation for showing toast notifications
    console.log(`Toast: [${severity}] ${message}`);
}

function updateStats() {
    // Update stats counters based on current data
    // This would be implemented with actual data from the server
}

// Initialize markers map
const markers = new Map();

function getOrCreateMarker(shipmentId) {
    if (!markers.has(shipmentId)) {
        const marker = L.marker([0, 0], {
            icon: L.divIcon({
                className: 'shipment-marker',
                html: '<i class="fas fa-truck"></i>',
                iconSize: [30, 30]
            })
        }).addTo(map);
        markers.set(shipmentId, marker);
    }
    return markers.get(shipmentId);
}