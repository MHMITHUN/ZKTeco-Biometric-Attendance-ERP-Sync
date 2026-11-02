# ZKTeco Biometric Time-Attendance & MySQL ERP Sync Engine

[![Live Demo](https://img.shields.io/badge/Demo-Live%20Biometric%20Hub-10b981)](https://mhmithun.github.io/ZKTeco-Biometric-Attendance-ERP-Sync/)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Database: MySQL](https://img.shields.io/badge/Database-MySQL%20%7C%20MariaDB-orange.svg)](zk_core/schema.sql)

Enterprise automated biometric data synchronization pipeline interfacing factory floor ZKTeco facial recognition and optical fingerprint terminals (TCP Port 4370 & ADMS Push) with central MySQL HRMS / ERP databases. Includes local SQLite offline failover buffering to guarantee zero punch loss during network interruptions.

---

## ⚡ Architecture & Live Web Simulator

The project includes an **interactive Biometric Turnstile Web Console** (`index.html`):
- **Live Biometric Hardware Emulator**: Simulate face and fingerprint recognition punches across factory gates and admin HQ turnstiles.
- **TCP/IP ADMS Packet Inspector**: Live viewing of structured JSON payloads transmitted to MySQL.
- **Reconciled Attendance Ledger**: Real-time evaluation of shift rules (On-time, grace period, late entry flags).

---

## 🛠️ Key Capabilities & Technical Features

1. **Python Biometric Polling & ADMS Daemon (`zk_core/zk_sync_daemon.py`)**:
   - Communicates with ZKTeco ProFace X, SilkBio, and SpeedFace devices over raw TCP socket port 4370.
   - Extracts device user rosters, attendance logs, and verification confidence scores.
   - Applies enterprise shift logic: 08:00 AM standard start, 15-minute grace period, late flag tracking.

2. **ACID Offline Failover Cache (`zk_core/offline_cache.py`)**:
   - Local SQLite queue buffers punches if network connection to central MySQL drops.
   - Automatic drain worker reconciles offline punches immediately upon network restoration.

3. **Production MySQL HRMS Schema (`zk_core/schema.sql`)**:
   - Normalized relational tables: `employees`, `zk_terminals`, `attendance_punches`, and `daily_shift_summary`.
   - Optimized compound indexes for sub-second query performance during payroll generation.

---

## 🚀 Quick Start

### 1. Run the Interactive Web Console
```bash
# Simply open index.html in your browser or run:
python -m http.server 8081
# Navigate to http://localhost:8081
```

### 2. Run the Python Sync Engine
```bash
# Clone the repository
git clone https://github.com/MHMITHUN/ZKTeco-Biometric-Attendance-ERP-Sync.git
cd ZKTeco-Biometric-Attendance-ERP-Sync

# Run the attendance sync daemon
python zk_core/zk_sync_daemon.py

# Test offline SQLite queue caching
python zk_core/offline_cache.py
```

---

## 👤 Author

**MD. Mahamudul Hasan**  
- **Role**: IT Officer  
- **Email**: mhmmithun1@gmail.com  
- **Phone**: +880 1560-027539  
- **LinkedIn**: [linkedin.com/in/mahamudul0](https://linkedin.com/in/mahamudul0)  
- **GitHub**: [github.com/MHMITHUN](https://github.com/MHMITHUN)  
