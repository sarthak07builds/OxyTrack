-- OxyTrack Database Schema
CREATE DATABASE IF NOT EXISTS oxytrack_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE oxytrack_db;

-- 1. Cylinders Table
CREATE TABLE IF NOT EXISTS cylinders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cylinder_code VARCHAR(50) NOT NULL UNIQUE,
    cylinder_type ENUM('Type A', 'Type B', 'Type C', 'Type D', 'Type E', 'Jumbo') NOT NULL DEFAULT 'Type D',
    water_capacity_liters DECIMAL(8, 2) NOT NULL DEFAULT 46.7, -- Geometric volume (V)
    max_pressure_bar DECIMAL(8, 2) NOT NULL DEFAULT 150.0,
    current_pressure_bar DECIMAL(8, 2) NOT NULL DEFAULT 150.0,
    temperature_celsius DECIMAL(5, 2) NOT NULL DEFAULT 25.0,
    flow_rate_lpm DECIMAL(8, 2) NOT NULL DEFAULT 0.0, -- Liters per minute consumed
    current_volume_liters DECIMAL(10, 2) NOT NULL DEFAULT 0.0,
    remaining_duration_minutes DECIMAL(10, 2) NOT NULL DEFAULT 0.0,
    status ENUM('Available', 'In Use', 'Depleted', 'Maintenance', 'Reserved') NOT NULL DEFAULT 'Available',
    location VARCHAR(100) NOT NULL DEFAULT 'Main Storage',
    assigned_patient VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. Monitoring Logs (Telemetry / History)
CREATE TABLE IF NOT EXISTS cylinder_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cylinder_id INT NOT NULL,
    pressure_bar DECIMAL(8, 2) NOT NULL,
    temperature_celsius DECIMAL(5, 2) NOT NULL,
    flow_rate_lpm DECIMAL(8, 2) NOT NULL,
    volume_liters DECIMAL(10, 2) NOT NULL,
    remaining_duration_minutes DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cylinder_id) REFERENCES cylinders(id) ON DELETE CASCADE
);

-- 3. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cylinder_id INT NOT NULL,
    alert_type ENUM('CRITICAL_LOW_PRESSURE', 'RAPID_LEAK', 'HIGH_PRESSURE', 'DEPLETED', 'MAINTENANCE_REQUIRED') NOT NULL,
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'MEDIUM',
    message TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (cylinder_id) REFERENCES cylinders(id) ON DELETE CASCADE
);

-- Sample Seed Data
INSERT INTO cylinders (cylinder_code, cylinder_type, water_capacity_liters, max_pressure_bar, current_pressure_bar, temperature_celsius, flow_rate_lpm, current_volume_liters, remaining_duration_minutes, status, location, assigned_patient)
VALUES
('OXY-ICU-101', 'Type D', 46.7, 150.0, 135.0, 24.5, 4.0, 6304.50, 1576.12, 'In Use', 'ICU Ward 1 - Bed 4', 'John Doe (ID: 9021)'),
('OXY-ICU-102', 'Type D', 46.7, 150.0, 32.0, 25.0, 5.0, 1494.40, 298.88, 'In Use', 'ICU Ward 1 - Bed 6', 'Sarah Connor (ID: 8812)'),
('OXY-ER-201', 'Type E', 4.7, 137.0, 120.0, 23.0, 2.5, 564.00, 225.60, 'In Use', 'Emergency Room - Bay 2', 'David Smith (ID: 4103)'),
('OXY-STO-301', 'Jumbo', 50.0, 200.0, 195.0, 22.0, 0.0, 9750.00, 0.00, 'Available', 'Central Depot', NULL),
('OXY-STO-302', 'Type D', 46.7, 150.0, 148.0, 23.5, 0.0, 6911.60, 0.00, 'Available', 'Ward 3 Storage', NULL),
('OXY-ISO-401', 'Type B', 10.2, 150.0, 12.0, 26.0, 3.0, 122.40, 40.80, 'Depleted', 'Isolation Ward - Room 12', 'Emma Watson (ID: 7721)')
ON DUPLICATE KEY UPDATE cylinder_code=cylinder_code;
