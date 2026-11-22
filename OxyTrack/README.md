# OxyTrack – Oxygen Cylinder Monitoring and Management System

OxyTrack is a medical oxygen monitoring and management system designed for hospitals, emergency response units, and medical depots to monitor oxygen cylinder telemetry, expanded gas volumes, time-to-empty calculations, and alert triggers in real time.

---

## 🌟 Key Features

1. **Live Fleet Dashboard**:
   - Total cylinder inventory status, active bedside usage count, and total volume stored (Liters STP).
   - Real-time pressure distribution and usage charts powered by **Chart.js**.
2. **Medical Gas Physics Engine**:
   - Volume calculation based on water capacity and pressure: \( V = V_{\text{water}} \times P \).
   - Usable duration projection factoring in safety residual pressure thresholds (10-15 bar) to avoid zero-flow collapse: \( \text{Duration} = \frac{V_{\text{usable}}}{\text{Flow Rate}} \).
3. **Cylinder Management**:
   - Add new cylinders across multiple types (Type D, Type E, Type B, Jumbo, etc.).
   - Telemetry updating for pressure drops, flow rates (L/min), and patient bed allocations.
   - Dynamic status transitions (`Available`, `In Use`, `Depleted`, `Maintenance`).
4. **Automated Safety Alerts**:
   - Real-time triggers for critical low pressure (< 15% threshold) or depletion.
   - Interactive resolution workflows.
5. **Gunicorn Production-Ready**:
   - Includes production-grade `gunicorn.conf.py` worker configuration.

---

## 🏗️ Technology Stack

- **Frontend**: HTML5, Modern CSS, Bootstrap 5, Bootstrap Icons, Chart.js
- **Backend**: Python 3.10+, Flask
- **Database**: MySQL with connection pooling (`mysql-connector-python`)
- **Server Deployment**: Gunicorn

---

## 🚀 Setup & Installation

### 1. Configure MySQL Database
Make sure your MySQL service is running. You can update database credentials in `.env`:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=oxytrack_db
DB_PORT=3306
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database
You can initialize the schema directly in MySQL:
```bash
mysql -u root -p < sql/schema.sql
```
*(Note: OxyTrack also auto-executes the schema on application startup if the database exists).*

### 4. Run Development Server
```bash
python app.py
```
Open your browser and navigate to:
```
http://localhost:5000
```

### 5. Run with Gunicorn (Production)
```bash
gunicorn -c gunicorn.conf.py app:app
```
