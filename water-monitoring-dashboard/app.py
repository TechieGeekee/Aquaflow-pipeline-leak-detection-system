# pip install -r requirements.txt

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
from firebase_config import initialize_firebase, get_system_data, get_firebase_ref
import os
import threading
import time
import queue
import hashlib
from collections import defaultdict

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Initialize Firebase
firebase_initialized = initialize_firebase()

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Store active alerts in memory
active_alerts = []
alert_history = []

# Track leak assignments to mechanics
leak_assignments = {}  # Format: {leak_id: mechanic_id}
mechanic_assigned_leaks = defaultdict(list)  # Format: {mechanic_id: [leak_id1, leak_id2]}

# SSE clients management
sse_clients = []
sse_lock = threading.Lock()

# User roles
class UserRole:
    ADMIN = 'admin'
    MECHANIC = 'mechanic'

# Predefined admin credentials
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': generate_password_hash('WaterMonitor2024!'),
    'role': UserRole.ADMIN,
    'name': 'Administrator'
}

# Predefined maintenance employees (in production, use database)
MAINTENANCE_EMPLOYEES = {
    'M001': {
        'id': 'M001',
        'password': generate_password_hash('mechanic001'),  # Default password
        'role': UserRole.MECHANIC,
        'name': 'John Smith',
        'phone': '+1-555-0101',
        'specialization': 'Pipe Leaks',
        'assigned_leaks': []
    },
    'M002': {
        'id': 'M002',
        'password': generate_password_hash('mechanic002'),
        'role': UserRole.MECHANIC,
        'name': 'Jane Doe',
        'phone': '+1-555-0102',
        'specialization': 'Valve Maintenance',
        'assigned_leaks': []
    },
    'M003': {
        'id': 'M003',
        'password': generate_password_hash('mechanic003'),
        'role': UserRole.MECHANIC,
        'name': 'Robert Johnson',
        'phone': '+1-555-0103',
        'specialization': 'Sensor Calibration',
        'assigned_leaks': []
    }
}

# Valve and pipe name mappings
VALVE_NAMES = {
    "TANK_VALVE": "Main Supply Valve",
    "VALVE_A": "Distribution Zone Valve"
}

PIPE_NAMES = {
    "TANK-S1": "Main Supply Line (Tank to Station 1)",
    "S1-S2": "Primary Distribution Line (Station 1 to Station 2)",
    "S2-VALVE_A": "Control Valve Supply Line",
    "VALVE_A-S3": "Zone A - Branch Line 1",
    "S3-TAP1": "Zone A - Tap 1 Supply Line",
    "VALVE_A-S4": "Zone A - Branch Line 2",
    "S4-TAP2": "Zone A - Tap 2 Supply Line",
    "VALVE_A-S5": "Main Distribution Trunk",
    "S5-JUNCTION_E": "Junction Supply Line",
    "JUNCTION_E-S6": "Zone B - Branch Line 1",
    "S6-TAP3": "Zone B - Tap 3 Supply Line",
    "JUNCTION_E-S7": "Zone B - Branch Line 2",
    "S7-TAP4": "Zone B - Tap 4 Supply Line",
    "JUNCTION_E-S8": "Zone B - Branch Line 3",
    "S8-TAP5": "Zone B - Tap 5 Supply Line"
}

TAP_NAMES = {
    "TAP1": "Kitchen Sink",
    "TAP2": "Bathroom Sink",
    "TAP3": "Garden Tap",
    "TAP4": "Laundry Room",
    "TAP5": "Emergency Supply"
}

# User class for Flask-Login with role support
class User(UserMixin):
    def __init__(self, id, role, name):
        self.id = id
        self.role = role
        self.name = name
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def is_mechanic(self):
        return self.role == UserRole.MECHANIC

@login_manager.user_loader
def load_user(user_id):
    # Check if it's admin
    if user_id == 'admin':
        return User('admin', UserRole.ADMIN, 'Administrator')
    
    # Check if it's a mechanic
    if user_id in MAINTENANCE_EMPLOYEES:
        employee = MAINTENANCE_EMPLOYEES[user_id]
        return User(user_id, UserRole.MECHANIC, employee['name'])
    
    return None

def get_available_mechanic():
    """Get the mechanic with the least assigned leaks (round-robin assignment)"""
    if not MAINTENANCE_EMPLOYEES:
        return None
    
    # Find mechanic with minimum assigned leaks
    min_leaks = float('inf')
    available_mechanics = []
    
    for mechanic_id in MAINTENANCE_EMPLOYEES:
        assigned_count = len(mechanic_assigned_leaks.get(mechanic_id, []))
        if assigned_count < min_leaks:
            min_leaks = assigned_count
            available_mechanics = [mechanic_id]
        elif assigned_count == min_leaks:
            available_mechanics.append(mechanic_id)
    
    if available_mechanics:
        # Return first available mechanic (for round-robin, you could rotate)
        return available_mechanics[0]
    
    return None

def assign_leak_to_mechanic(leak_id, pipe_name):
    """Assign a leak to a mechanic"""
    mechanic_id = get_available_mechanic()
    
    if mechanic_id:
        leak_assignments[leak_id] = mechanic_id
        mechanic_assigned_leaks[mechanic_id].append(leak_id)
        
        # Update employee record
        if leak_id not in MAINTENANCE_EMPLOYEES[mechanic_id]['assigned_leaks']:
            MAINTENANCE_EMPLOYEES[mechanic_id]['assigned_leaks'].append(leak_id)
        
        print(f"Leak '{pipe_name}' assigned to mechanic {mechanic_id} ({MAINTENANCE_EMPLOYEES[mechanic_id]['name']})")
        return mechanic_id
    
    return None

def unassign_leak(leak_id):
    """Remove leak assignment"""
    if leak_id in leak_assignments:
        mechanic_id = leak_assignments[leak_id]
        
        # Remove from mechanic's assigned leaks
        if leak_id in mechanic_assigned_leaks[mechanic_id]:
            mechanic_assigned_leaks[mechanic_id].remove(leak_id)
        
        # Remove from employee record
        if leak_id in MAINTENANCE_EMPLOYEES[mechanic_id]['assigned_leaks']:
            MAINTENANCE_EMPLOYEES[mechanic_id]['assigned_leaks'].remove(leak_id)
        
        # Remove from leak assignments
        del leak_assignments[leak_id]
        
        return mechanic_id
    return None

def get_assigned_leaks_for_mechanic(mechanic_id):
    """Get all leaks assigned to a specific mechanic"""
    if mechanic_id not in mechanic_assigned_leaks:
        return []
    
    assigned_leak_ids = mechanic_assigned_leaks[mechanic_id]
    mechanic_leaks = []
    
    for alert in active_alerts:
        if alert['id'] in assigned_leak_ids:
            mechanic_leaks.append(alert)
    
    return mechanic_leaks

def broadcast_update(data):
    """Broadcast update to all connected SSE clients"""
    with sse_lock:
        disconnected = []
        for client_queue in sse_clients:
            try:
                client_queue.put(data, block=False)
            except queue.Full:
                disconnected.append(client_queue)
        
        # Remove disconnected clients
        for client in disconnected:
            sse_clients.remove(client)

def broadcast_to_mechanic(mechanic_id, data):
    """Send update to specific mechanic (if they're connected)"""
    # This is a simplified version - in production, you'd track which client is which mechanic
    # For now, we'll broadcast to all and let the client-side filter
    broadcast_update({
        'type': 'mechanic_update',
        'mechanic_id': mechanic_id,
        'data': data
    })

def monitor_leaks():
    """Background thread to monitor for leaks and update alerts"""
    prev_system_data = {}
    mechanic_index = 0  # For round-robin assignment
    
    while True:
        try:
            system_data = get_system_data()
            data_changed = False
            
            if 'active_leaks' in system_data:
                for pipe_id, status in system_data['active_leaks'].items():
                    if status == 1:  # Active leak
                        pipe_name = PIPE_NAMES.get(pipe_id, pipe_id)
                        leak_id = f"leak_{pipe_id}"
                        
                        # Check if this leak is already in active alerts
                        existing_alert = next((a for a in active_alerts if a['id'] == leak_id), None)
                        
                        if not existing_alert:
                            # Assign leak to a mechanic
                            mechanic_id = assign_leak_to_mechanic(leak_id, pipe_name)
                            mechanic_name = MAINTENANCE_EMPLOYEES[mechanic_id]['name'] if mechanic_id else "Unassigned"
                            
                            # Create new alert
                            alert = {
                                'id': leak_id,
                                'type': 'leak',
                                'title': f"🚨 ACTIVE LEAK DETECTED",
                                'message': f"Leak detected in: {pipe_name}",
                                'pipe_id': pipe_id,
                                'pipe_name': pipe_name,
                                'timestamp': datetime.now().isoformat(),
                                'severity': 'high',
                                'acknowledged': False,
                                'assigned_mechanic_id': mechanic_id,
                                'assigned_mechanic_name': mechanic_name,
                                'status': 'assigned' if mechanic_id else 'unassigned'
                            }
                            active_alerts.append(alert)
                            
                            # Add to history
                            alert_history.append({
                                **alert,
                                'resolved_at': None,
                                'resolved': False
                            })
                            
                            print(f"New leak alert: {pipe_name} assigned to {mechanic_name}")
                            data_changed = True
                            
                            # Notify assigned mechanic
                            if mechanic_id:
                                broadcast_to_mechanic(mechanic_id, {
                                    'type': 'new_assignment',
                                    'alert': alert
                                })
                    else:
                        # If leak is resolved, move from active to history
                        leak_id = f"leak_{pipe_id}"
                        existing_alert = next((a for a in active_alerts if a['id'] == leak_id), None)
                        
                        if existing_alert:
                            # Get assigned mechanic before removing
                            mechanic_id = existing_alert.get('assigned_mechanic_id')
                            
                            # Move to history as resolved
                            active_alerts.remove(existing_alert)
                            for history_alert in alert_history:
                                if history_alert['id'] == leak_id and not history_alert.get('resolved'):
                                    history_alert['resolved'] = True
                                    history_alert['resolved_at'] = datetime.now().isoformat()
                                    history_alert['status'] = 'resolved'
                                    print(f"Leak resolved: {existing_alert['pipe_name']}")
                            
                            # Unassign the leak
                            if mechanic_id:
                                unassign_leak(leak_id)
                                # Notify mechanic
                                broadcast_to_mechanic(mechanic_id, {
                                    'type': 'assignment_resolved',
                                    'leak_id': leak_id
                                })
                            
                            data_changed = True
            
            # Check for other system anomalies
            anomaly_changed = check_system_anomalies(system_data)
            
            # Check if any system data changed
            if system_data != prev_system_data or data_changed or anomaly_changed:
                # Broadcast update to all connected clients
                update_data = get_processed_system_data(system_data)
                broadcast_update({
                    'type': 'system_update',
                    'data': update_data
                })
                prev_system_data = system_data.copy()
            
        except Exception as e:
            print(f"Error in leak monitoring: {e}")
        
        time.sleep(2)  # Check every 2 seconds for faster updates

def check_system_anomalies(system_data):
    """Check for other system anomalies"""
    data_changed = False
    
    # Check for low water level (only for admin)
    water_level = system_data.get('water_level', 0)
    if water_level < 20:  # Assuming 20% is low
        alert_id = "low_water_level"
        existing_alert = next((a for a in active_alerts if a['id'] == alert_id), None)
        
        if not existing_alert:
            alert = {
                'id': alert_id,
                'type': 'water_level',
                'title': f"⚠️ LOW WATER LEVEL",
                'message': f"Water level is critically low: {water_level}%",
                'level': water_level,
                'timestamp': datetime.now().isoformat(),
                'severity': 'medium',
                'acknowledged': False,
                'assigned_mechanic_id': None,
                'assigned_mechanic_name': None,
                'status': 'unassigned'  # Water level alerts are for admin only
            }
            active_alerts.append(alert)
            
            alert_history.append({
                **alert,
                'resolved_at': None,
                'resolved': False
            })
            data_changed = True
    else:
        # If water level is back to normal, resolve the alert
        alert_id = "low_water_level"
        existing_alert = next((a for a in active_alerts if a['id'] == alert_id), None)
        if existing_alert:
            active_alerts.remove(existing_alert)
            for history_alert in alert_history:
                if history_alert['id'] == alert_id and not history_alert.get('resolved'):
                    history_alert['resolved'] = True
                    history_alert['resolved_at'] = datetime.now().isoformat()
                    history_alert['status'] = 'resolved'
            data_changed = True
    
    return data_changed

def get_processed_system_data(system_data):
    """Process system data for API response"""
    processed_data = {
        'valves': {},
        'sensors': system_data.get('sensors', {}),
        'water_level': system_data.get('water_level', 0),
        'taps': {},
        'leaks': {},
        'active_alerts': active_alerts,
        'unacknowledged_alerts': len([a for a in active_alerts if not a.get('acknowledged')]),
        'timestamp': system_data.get('timestamp', datetime.now().isoformat())
    }
    
    # Map valve names
    if 'valves' in system_data:
        for valve_id, status in system_data['valves'].items():
            valve_name = VALVE_NAMES.get(valve_id, valve_id)
            processed_data['valves'][valve_name] = status
    
    # Map tap names
    if 'taps' in system_data:
        for tap_id, status in system_data['taps'].items():
            tap_name = TAP_NAMES.get(tap_id, tap_id)
            processed_data['taps'][tap_name] = status
    
    # Map leak names from system data
    if 'active_leaks' in system_data:
        for pipe_id, status in system_data['active_leaks'].items():
            if status == 1:  # Only active leaks
                pipe_name = PIPE_NAMES.get(pipe_id, pipe_id)
                processed_data['leaks'][pipe_name] = "ACTIVE"
    
    return processed_data

# Start leak monitoring in background thread
if firebase_initialized:
    monitor_thread = threading.Thread(target=monitor_leaks, daemon=True)
    monitor_thread.start()
    print("Leak monitoring started")

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('mechanic_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('mechanic_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if admin login
        if username == 'admin' and check_password_hash(ADMIN_CREDENTIALS['password'], password):
            user = User('admin', UserRole.ADMIN, 'Administrator')
            login_user(user)
            flash('Admin login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        # Check if mechanic login
        elif username in MAINTENANCE_EMPLOYEES:
            employee = MAINTENANCE_EMPLOYEES[username]
            if check_password_hash(employee['password'], password):
                user = User(username, UserRole.MECHANIC, employee['name'])
                login_user(user)
                flash(f'Welcome, {employee["name"]}!', 'success')
                return redirect(url_for('mechanic_dashboard'))
        
        flash('Invalid credentials. Please try again.', 'danger')
    
    return render_template('login.html', show_employee_id_field=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('mechanic_dashboard'))
    
    system_data = get_system_data()
    
    # Process data for display
    valve_status = {}
    if 'valves' in system_data:
        for valve_id, status in system_data['valves'].items():
            valve_name = VALVE_NAMES.get(valve_id, valve_id)
            valve_status[valve_name] = "Open" if status == 1 else "Closed"
    
    # Process sensor data
    sensors = system_data.get('sensors', {})
    
    # Process water level
    water_level = system_data.get('water_level', 0)
    
    # Process tap status
    tap_status = {}
    if 'taps' in system_data:
        for tap_id, status in system_data['taps'].items():
            tap_name = TAP_NAMES.get(tap_id, tap_id)
            tap_status[tap_name] = "Open" if status == 1 else "Closed"
    
    # Check for leaks from system data
    current_leaks = {}
    if 'active_leaks' in system_data:
        for pipe_id, status in system_data['active_leaks'].items():
            if status == 1:  # Active leak
                pipe_name = PIPE_NAMES.get(pipe_id, pipe_id)
                current_leaks[pipe_name] = "ACTIVE LEAK"
    
    # Get active alerts (includes leaks and other alerts)
    active_alerts_count = len([a for a in active_alerts if not a.get('acknowledged')])
    
    # Get mechanic assignments summary
    mechanic_workload = {}
    for mechanic_id, employee in MAINTENANCE_EMPLOYEES.items():
        assigned_leaks = mechanic_assigned_leaks.get(mechanic_id, [])
        mechanic_workload[employee['name']] = {
            'id': mechanic_id,
            'assigned_count': len(assigned_leaks),
            'leaks': assigned_leaks,
            'specialization': employee['specialization']
        }
    
    return render_template('dashboard.html',
                         valve_status=valve_status,
                         sensors=sensors,
                         water_level=water_level,
                         tap_status=tap_status,
                         leaks=current_leaks,
                         firebase_connected=firebase_initialized,
                         last_update=system_data.get('timestamp', 'N/A'),
                         active_alerts_count=active_alerts_count,
                         mechanic_workload=mechanic_workload,
                         current_user=current_user)

@app.route('/mechanic/dashboard')
@login_required
def mechanic_dashboard():
    if not current_user.is_mechanic():
        flash('Access denied. Mechanics only.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get assigned leaks for this mechanic
    assigned_leaks = get_assigned_leaks_for_mechanic(current_user.id)
    
    # Get mechanic details
    mechanic_details = MAINTENANCE_EMPLOYEES.get(current_user.id, {})
    
    return render_template('mechanic_dashboard.html',
                         assigned_leaks=assigned_leaks,
                         mechanic_details=mechanic_details,
                         current_user=current_user,
                         firebase_connected=firebase_initialized)

@app.route('/stream')
@login_required
def stream():
    """Server-Sent Events endpoint for real-time updates"""
    def event_stream():
        # Create a queue for this client
        client_queue = queue.Queue(maxsize=10)
        
        with sse_lock:
            sse_clients.append(client_queue)
        
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Stream connected'})}\n\n"
            
            # Keep connection alive and send updates
            while True:
                try:
                    # Wait for update with timeout to send keepalive
                    message = client_queue.get(timeout=30)
                    
                    # If mechanic, filter only relevant messages
                    if current_user.is_mechanic():
                        # Only send mechanic-specific updates and general pings
                        if (message.get('type') == 'ping' or 
                            message.get('type') == 'mechanic_update' and 
                            message.get('mechanic_id') == current_user.id):
                            yield f"data: {json.dumps(message)}\n\n"
                    else:
                        # Admin gets everything
                        yield f"data: {json.dumps(message)}\n\n"
                        
                except queue.Empty:
                    # Send keepalive ping
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        except GeneratorExit:
            # Client disconnected
            with sse_lock:
                if client_queue in sse_clients:
                    sse_clients.remove(client_queue)
    
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/api/system-data')
@login_required
def api_system_data():
    """API endpoint for real-time data updates"""
    system_data = get_system_data()
    
    if current_user.is_mechanic():
        # For mechanics, only return their assigned leaks
        mechanic_leaks = get_assigned_leaks_for_mechanic(current_user.id)
        processed_data = get_processed_system_data(system_data)
        
        # Filter to only show mechanic's assigned leaks
        filtered_alerts = [alert for alert in processed_data['active_alerts'] 
                          if alert.get('assigned_mechanic_id') == current_user.id]
        
        processed_data['active_alerts'] = filtered_alerts
        processed_data['unacknowledged_alerts'] = len([a for a in filtered_alerts if not a.get('acknowledged')])
    else:
        # Admin gets everything
        processed_data = get_processed_system_data(system_data)
    
    return jsonify(processed_data)

@app.route('/api/alerts')
@login_required
def get_alerts():
    """Get all active alerts (filtered for mechanics)"""
    if current_user.is_mechanic():
        # Mechanics only see their assigned alerts
        mechanic_alerts = get_assigned_leaks_for_mechanic(current_user.id)
        return jsonify({
            'active_alerts': mechanic_alerts,
            'unacknowledged_count': len([a for a in mechanic_alerts if not a.get('acknowledged')]),
            'total_active': len(mechanic_alerts),
            'timestamp': datetime.now().isoformat()
        })
    else:
        # Admin sees everything
        return jsonify({
            'active_alerts': active_alerts,
            'unacknowledged_count': len([a for a in active_alerts if not a.get('acknowledged')]),
            'total_active': len(active_alerts),
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/alerts/acknowledge', methods=['POST'])
@login_required
def acknowledge_alert():
    """Acknowledge an alert"""
    data = request.get_json()
    alert_id = data.get('alert_id')
    
    if current_user.is_mechanic():
        # Mechanics can only acknowledge their assigned alerts
        for alert in active_alerts:
            if alert['id'] == alert_id and alert.get('assigned_mechanic_id') == current_user.id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.now().isoformat()
                alert['acknowledged_by'] = current_user.name
                
                # Update history
                for history_alert in alert_history:
                    if history_alert['id'] == alert_id and not history_alert.get('resolved'):
                        history_alert['acknowledged'] = True
                        history_alert['acknowledged_at'] = datetime.now().isoformat()
                        history_alert['acknowledged_by'] = current_user.name
                
                # Broadcast update
                system_data = get_system_data()
                broadcast_update({
                    'type': 'alert_acknowledged',
                    'alert_id': alert_id,
                    'acknowledged_by': current_user.name,
                    'data': get_processed_system_data(system_data)
                })
                
                return jsonify({'success': True, 'message': 'Alert acknowledged'})
        
        return jsonify({'success': False, 'message': 'Alert not found or not assigned to you'}), 403
    
    else:
        # Admin can acknowledge any alert
        for alert in active_alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.now().isoformat()
                alert['acknowledged_by'] = 'Admin'
                
                # Update history
                for history_alert in alert_history:
                    if history_alert['id'] == alert_id and not history_alert.get('resolved'):
                        history_alert['acknowledged'] = True
                        history_alert['acknowledged_at'] = datetime.now().isoformat()
                        history_alert['acknowledged_by'] = 'Admin'
                
                # Broadcast update
                system_data = get_system_data()
                broadcast_update({
                    'type': 'alert_acknowledged',
                    'alert_id': alert_id,
                    'acknowledged_by': 'Admin',
                    'data': get_processed_system_data(system_data)
                })
                
                return jsonify({'success': True, 'message': 'Alert acknowledged'})
    
    return jsonify({'success': False, 'message': 'Alert not found'}), 404

@app.route('/api/alerts/history')
@login_required
def get_alert_history():
    """Get alert history"""
    if current_user.is_mechanic():
        # Mechanics only see their assigned alert history
        mechanic_history = [
            alert for alert in alert_history 
            if alert.get('assigned_mechanic_id') == current_user.id
        ]
        return jsonify({
            'history': mechanic_history[-50:],  # Last 50 alerts
            'total_count': len(mechanic_history)
        })
    else:
        # Admin sees everything
        return jsonify({
            'history': alert_history[-50:],  # Last 50 alerts
            'total_count': len(alert_history)
        })

@app.route('/api/alerts/resolve-all', methods=['POST'])
@login_required
def resolve_all_alerts():
    """Mark all alerts as resolved (admin only)"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin only'}), 403
    
    for alert in active_alerts:
        alert['resolved'] = True
        alert['resolved_at'] = datetime.now().isoformat()
        alert['resolved_by'] = current_user.name
    
    # Move all to history as resolved
    for alert in active_alerts[:]:
        for history_alert in alert_history:
            if history_alert['id'] == alert['id'] and not history_alert.get('resolved'):
                history_alert['resolved'] = True
                history_alert['resolved_at'] = datetime.now().isoformat()
                history_alert['resolved_by'] = current_user.name
    
    active_alerts.clear()
    leak_assignments.clear()
    mechanic_assigned_leaks.clear()
    
    # Clear assigned_leaks from employees
    for mechanic_id in MAINTENANCE_EMPLOYEES:
        MAINTENANCE_EMPLOYEES[mechanic_id]['assigned_leaks'] = []
    
    # Broadcast update
    system_data = get_system_data()
    broadcast_update({
        'type': 'alerts_resolved',
        'data': get_processed_system_data(system_data)
    })
    
    return jsonify({
        'success': True,
        'message': 'All alerts resolved',
        'remaining_alerts': len(active_alerts)
    })

@app.route('/api/simulate-leak', methods=['POST'])
@login_required
def simulate_leak():
    """Simulate a leak for testing (admin only)"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin only'}), 403
    
    if app.debug or os.environ.get('FLASK_ENV') == 'development':
        data = request.get_json()
        pipe_id = data.get('pipe_id', 'TANK-S1')
        active = data.get('active', True)
        
        pipe_name = PIPE_NAMES.get(pipe_id, pipe_id)
        leak_id = f"leak_{pipe_id}"
        
        if active:
            # Assign leak to a mechanic
            mechanic_id = assign_leak_to_mechanic(leak_id, pipe_name)
            mechanic_name = MAINTENANCE_EMPLOYEES[mechanic_id]['name'] if mechanic_id else "Unassigned"
            
            # Create leak alert
            alert = {
                'id': leak_id,
                'type': 'leak',
                'title': f"🚨 SIMULATED LEAK DETECTED",
                'message': f"Simulated leak in: {pipe_name}",
                'pipe_id': pipe_id,
                'pipe_name': pipe_name,
                'timestamp': datetime.now().isoformat(),
                'severity': 'high',
                'acknowledged': False,
                'assigned_mechanic_id': mechanic_id,
                'assigned_mechanic_name': mechanic_name,
                'status': 'assigned' if mechanic_id else 'unassigned',
                'simulated': True
            }
            
            # Remove if already exists
            existing_alert = next((a for a in active_alerts if a['id'] == leak_id), None)
            if existing_alert:
                active_alerts.remove(existing_alert)
            
            active_alerts.append(alert)
            
            # Broadcast update
            system_data = get_system_data()
            broadcast_update({
                'type': 'leak_detected',
                'data': get_processed_system_data(system_data)
            })
            
            return jsonify({
                'success': True,
                'message': f'Simulated leak created for {pipe_name} assigned to {mechanic_name}',
                'alert': alert
            })
        else:
            # Resolve leak
            alert_to_remove = next((a for a in active_alerts if a['id'] == leak_id), None)
            if alert_to_remove:
                active_alerts.remove(alert_to_remove)
                
                # Unassign leak
                mechanic_id = unassign_leak(leak_id)
                
                # Broadcast update
                system_data = get_system_data()
                broadcast_update({
                    'type': 'leak_resolved',
                    'data': get_processed_system_data(system_data)
                })
                
                return jsonify({
                    'success': True,
                    'message': f'Simulated leak resolved for {pipe_name}'
                })
    
    return jsonify({'success': False, 'message': 'Not allowed in production'}), 403

@app.route('/api/mechanics')
@login_required
def get_mechanics():
    """Get list of mechanics (admin only)"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin only'}), 403
    
    mechanics_list = []
    for mechanic_id, details in MAINTENANCE_EMPLOYEES.items():
        assigned_count = len(mechanic_assigned_leaks.get(mechanic_id, []))
        mechanics_list.append({
            'id': mechanic_id,
            'name': details['name'],
            'specialization': details['specialization'],
            'phone': details['phone'],
            'assigned_leaks_count': assigned_count,
            'assigned_leaks': mechanic_assigned_leaks.get(mechanic_id, [])
        })
    
    return jsonify({
        'mechanics': mechanics_list,
        'total_mechanics': len(mechanics_list),
        'total_assigned_leaks': len(leak_assignments)
    })

@app.route('/api/assign-leak', methods=['POST'])
@login_required
def assign_leak():
    """Manually assign/reassign a leak (admin only)"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin only'}), 403
    
    data = request.get_json()
    leak_id = data.get('leak_id')
    mechanic_id = data.get('mechanic_id')
    
    if leak_id not in [alert['id'] for alert in active_alerts]:
        return jsonify({'success': False, 'message': 'Leak not found'}), 404
    
    if mechanic_id not in MAINTENANCE_EMPLOYEES:
        return jsonify({'success': False, 'message': 'Mechanic not found'}), 404
    
    # Unassign from current mechanic if any
    old_mechanic_id = unassign_leak(leak_id)
    
    # Assign to new mechanic
    leak_assignments[leak_id] = mechanic_id
    mechanic_assigned_leaks[mechanic_id].append(leak_id)
    
    # Update employee record
    if leak_id not in MAINTENANCE_EMPLOYEES[mechanic_id]['assigned_leaks']:
        MAINTENANCE_EMPLOYEES[mechanic_id]['assigned_leaks'].append(leak_id)
    
    # Update alert
    for alert in active_alerts:
        if alert['id'] == leak_id:
            alert['assigned_mechanic_id'] = mechanic_id
            alert['assigned_mechanic_name'] = MAINTENANCE_EMPLOYEES[mechanic_id]['name']
            alert['status'] = 'reassigned'
            break
    
    # Notify old mechanic (if any)
    if old_mechanic_id:
        broadcast_to_mechanic(old_mechanic_id, {
            'type': 'assignment_removed',
            'leak_id': leak_id
        })
    
    # Notify new mechanic
    broadcast_to_mechanic(mechanic_id, {
        'type': 'new_assignment',
        'leak_id': leak_id
    })
    
    return jsonify({
        'success': True,
        'message': f'Leak reassigned to {MAINTENANCE_EMPLOYEES[mechanic_id]["name"]}',
        'old_mechanic': old_mechanic_id,
        'new_mechanic': mechanic_id
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)