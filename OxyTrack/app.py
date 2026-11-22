from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from config import Config
from database import get_db_connection, setup_database_schema
from physics import calculate_oxygen_volume, calculate_remaining_time, determine_cylinder_status
from mysql.connector import Error
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Ensure database tables exist on startup
with app.app_context():
    setup_database_schema()

# --- WEB PAGES ---

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/cylinders')
def cylinders_view():
    return render_template('cylinders.html')

@app.route('/analytics')
def analytics_view():
    return render_template('analytics.html')

@app.route('/alerts')
def alerts_view():
    return render_template('alerts.html')


# --- REST API ENDPOINTS ---

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Returns high level summary KPI counts and averages"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) as total_cylinders FROM cylinders")
        total = cursor.fetchone()['total_cylinders']

        cursor.execute("SELECT COUNT(*) as in_use FROM cylinders WHERE status = 'In Use'")
        in_use = cursor.fetchone()['in_use']

        cursor.execute("SELECT COUNT(*) as available FROM cylinders WHERE status = 'Available'")
        available = cursor.fetchone()['available']

        cursor.execute("SELECT COUNT(*) as depleted FROM cylinders WHERE status = 'Depleted'")
        depleted = cursor.fetchone()['depleted']

        cursor.execute("SELECT COUNT(*) as active_alerts FROM alerts WHERE is_resolved = FALSE")
        active_alerts = cursor.fetchone()['active_alerts']

        cursor.execute("SELECT SUM(current_volume_liters) as total_volume_stored FROM cylinders")
        volume_res = cursor.fetchone()['total_volume_stored']
        total_volume = float(volume_res) if volume_res else 0.0

        cursor.close()
        return jsonify({
            "status": "success",
            "data": {
                "total_cylinders": total,
                "in_use": in_use,
                "available": available,
                "depleted": depleted,
                "active_alerts": active_alerts,
                "total_volume_stored_liters": round(total_volume, 2)
            }
        })
    except Error as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.route('/api/cylinders', methods=['GET'])
def list_cylinders():
    """List cylinders with optional status/search filters"""
    status_filter = request.args.get('status')
    search = request.args.get('search')
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM cylinders WHERE 1=1"
        params = []
        
        if status_filter:
            query += " AND status = %s"
            params.append(status_filter)
        if search:
            query += " AND (cylinder_code LIKE %s OR location LIKE %s OR assigned_patient LIKE %s)"
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])
            
        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Transform data types for clean JSON output
        cylinders = []
        for r in rows:
            percentage = round((float(r['current_pressure_bar']) / float(r['max_pressure_bar']) * 100.0), 1) if float(r['max_pressure_bar']) > 0 else 0
            time_calc = calculate_remaining_time(
                float(r['current_volume_liters']), 
                float(r['flow_rate_lpm']),
                water_capacity_liters=float(r['water_capacity_liters'])
            )
            cylinders.append({
                "id": r['id'],
                "cylinder_code": r['cylinder_code'],
                "cylinder_type": r['cylinder_type'],
                "water_capacity_liters": float(r['water_capacity_liters']),
                "max_pressure_bar": float(r['max_pressure_bar']),
                "current_pressure_bar": float(r['current_pressure_bar']),
                "pressure_percentage": percentage,
                "temperature_celsius": float(r['temperature_celsius']),
                "flow_rate_lpm": float(r['flow_rate_lpm']),
                "current_volume_liters": float(r['current_volume_liters']),
                "remaining_duration_minutes": time_calc['minutes'],
                "remaining_duration_formatted": time_calc['formatted'],
                "status": r['status'],
                "location": r['location'],
                "assigned_patient": r['assigned_patient'],
                "updated_at": r['updated_at'].strftime("%Y-%m-%d %H:%M:%S") if r['updated_at'] else None
            })
            
        cursor.close()
        return jsonify({"status": "success", "data": cylinders})
    except Error as e:
        logger.error(f"Error querying cylinders: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.route('/api/cylinders', methods=['POST'])
def add_cylinder():
    """Register a new oxygen cylinder"""
    data = request.get_json() or {}
    required_fields = ['cylinder_code', 'cylinder_type', 'water_capacity_liters', 'max_pressure_bar', 'current_pressure_bar']
    for rf in required_fields:
        if rf not in data:
            return jsonify({"status": "error", "message": f"Missing required field: {rf}"}), 400
            
    code = data['cylinder_code'].strip()
    c_type = data['cylinder_type']
    capacity = float(data['water_capacity_liters'])
    max_p = float(data['max_pressure_bar'])
    curr_p = float(data['current_pressure_bar'])
    temp = float(data.get('temperature_celsius', 25.0))
    flow = float(data.get('flow_rate_lpm', 0.0))
    location = data.get('location', 'Main Storage')
    patient = data.get('assigned_patient', None)
    initial_status = data.get('status', 'Available')

    # Calculate Volume & Remaining Time
    volume = calculate_oxygen_volume(capacity, curr_p)
    time_info = calculate_remaining_time(volume, flow, water_capacity_liters=capacity)
    status = determine_cylinder_status(curr_p, max_p, initial_status)

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO cylinders 
            (cylinder_code, cylinder_type, water_capacity_liters, max_pressure_bar, current_pressure_bar, 
             temperature_celsius, flow_rate_lpm, current_volume_liters, remaining_duration_minutes, status, location, assigned_patient)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (code, c_type, capacity, max_p, curr_p, temp, flow, volume, time_info['minutes'], status, location, patient))
        new_id = cursor.lastrowid

        # Insert telemetry log
        log_query = """
            INSERT INTO cylinder_logs (cylinder_id, pressure_bar, temperature_celsius, flow_rate_lpm, volume_liters, remaining_duration_minutes, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(log_query, (new_id, curr_p, temp, flow, volume, time_info['minutes'], status))
        
        conn.commit()
        cursor.close()
        return jsonify({"status": "success", "message": "Cylinder added successfully", "cylinder_id": new_id}), 201
    except Error as e:
        logger.error(f"Error adding cylinder: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.route('/api/cylinders/<int:cylinder_id>', methods=['PUT', 'PATCH'])
def update_cylinder(cylinder_id):
    """Updates telemetry (pressure, flow rate, patient assignment, status)"""
    data = request.get_json() or {}
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cylinders WHERE id = %s", (cylinder_id,))
        cyl = cursor.fetchone()
        if not cyl:
            cursor.close()
            return jsonify({"status": "error", "message": "Cylinder not found"}), 404

        # Read updated or existing values
        curr_p = float(data.get('current_pressure_bar', cyl['current_pressure_bar']))
        flow = float(data.get('flow_rate_lpm', cyl['flow_rate_lpm']))
        temp = float(data.get('temperature_celsius', cyl['temperature_celsius']))
        location = data.get('location', cyl['location'])
        patient = data.get('assigned_patient', cyl['assigned_patient'])
        req_status = data.get('status', cyl['status'])

        capacity = float(cyl['water_capacity_liters'])
        max_p = float(cyl['max_pressure_bar'])

        # Recalculate
        volume = calculate_oxygen_volume(capacity, curr_p)
        time_info = calculate_remaining_time(volume, flow, water_capacity_liters=capacity)
        status = determine_cylinder_status(curr_p, max_p, req_status)

        # Trigger automatic alert if critical pressure
        pressure_ratio = (curr_p / max_p) if max_p > 0 else 0
        if pressure_ratio <= 0.15 and status != 'Maintenance':
            cursor.execute("""
                INSERT INTO alerts (cylinder_id, alert_type, severity, message)
                VALUES (%s, 'CRITICAL_LOW_PRESSURE', 'CRITICAL', %s)
            """, (cylinder_id, f"Cylinder {cyl['cylinder_code']} is at {curr_p} bar ({round(pressure_ratio*100, 1)}%). Urgent replacement needed!"))

        update_query = """
            UPDATE cylinders 
            SET current_pressure_bar = %s,
                flow_rate_lpm = %s,
                temperature_celsius = %s,
                current_volume_liters = %s,
                remaining_duration_minutes = %s,
                status = %s,
                location = %s,
                assigned_patient = %s
            WHERE id = %s
        """
        cursor.execute(update_query, (curr_p, flow, temp, volume, time_info['minutes'], status, location, patient, cylinder_id))

        # Log entry
        cursor.execute("""
            INSERT INTO cylinder_logs (cylinder_id, pressure_bar, temperature_celsius, flow_rate_lpm, volume_liters, remaining_duration_minutes, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (cylinder_id, curr_p, temp, flow, volume, time_info['minutes'], status))

        conn.commit()
        cursor.close()
        return jsonify({"status": "success", "message": "Cylinder updated successfully"})
    except Error as e:
        logger.error(f"Error updating cylinder: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.route('/api/cylinders/<int:cylinder_id>', methods=['DELETE'])
def delete_cylinder(cylinder_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cylinders WHERE id = %s", (cylinder_id,))
        conn.commit()
        cursor.close()
        return jsonify({"status": "success", "message": "Cylinder deleted successfully"})
    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, c.cylinder_code, c.location 
            FROM alerts a
            JOIN cylinders c ON a.cylinder_id = c.id
            ORDER BY a.is_resolved ASC, a.created_at DESC
        """)
        alerts = cursor.fetchall()
        for a in alerts:
            a['created_at'] = a['created_at'].strftime("%Y-%m-%d %H:%M:%S") if a['created_at'] else None
            a['resolved_at'] = a['resolved_at'].strftime("%Y-%m-%d %H:%M:%S") if a['resolved_at'] else None
        cursor.close()
        return jsonify({"status": "success", "data": alerts})
    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET is_resolved = TRUE, resolved_at = NOW() WHERE id = %s", (alert_id,))
        conn.commit()
        cursor.close()
        return jsonify({"status": "success", "message": "Alert marked as resolved"})
    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.route('/api/analytics/charts', methods=['GET'])
def get_chart_data():
    """Provides consolidated aggregated series data for Chart.js dashboards"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Status distribution
        cursor.execute("SELECT status, COUNT(*) as count FROM cylinders GROUP BY status")
        status_dist = cursor.fetchall()

        # 2. Location distribution
        cursor.execute("SELECT location, COUNT(*) as count, SUM(current_volume_liters) as total_vol FROM cylinders GROUP BY location")
        location_dist = cursor.fetchall()

        # 3. Pressure ranges
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN current_pressure_bar < 30 THEN 1 ELSE 0 END) as critical_low,
                SUM(CASE WHEN current_pressure_bar >= 30 AND current_pressure_bar < 75 THEN 1 ELSE 0 END) as low,
                SUM(CASE WHEN current_pressure_bar >= 75 AND current_pressure_bar < 120 THEN 1 ELSE 0 END) as moderate,
                SUM(CASE WHEN current_pressure_bar >= 120 THEN 1 ELSE 0 END) as optimal
            FROM cylinders
        """)
        pressure_dist = cursor.fetchone()

        cursor.close()
        return jsonify({
            "status": "success",
            "data": {
                "status_distribution": status_dist,
                "location_distribution": location_dist,
                "pressure_distribution": pressure_dist
            }
        })
    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
