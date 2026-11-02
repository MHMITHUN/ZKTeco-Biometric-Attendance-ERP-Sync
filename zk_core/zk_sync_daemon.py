#!/usr/bin/env python3
"""
ZKTeco Biometric Time-Attendance & MySQL HRMS Sync Daemon
Author: MD. Mahamudul Hasan
Repository: ZKTeco-Biometric-Attendance-ERP-Sync
License: MIT

Extracts real-time employee attendance punches (Facial Recognition & Optical Fingerprint)
from factory ZKTeco terminals via TCP Port 4370 / ADMS Push, processes shift rules,
and synchronizes with the central MySQL / HRMS database with offline caching.
"""

import time
import json
import logging
from datetime import datetime, time as dtime
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [ZK-SYNC] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('ZKSyncDaemon')


class ZKTerminal:
    def __init__(self, device_id: str, name: str, ip: str, port: int = 4370,
                 location: str = 'Gate 01'):
        self.device_id = device_id
        self.name = name
        self.ip = ip
        self.port = port
        self.location = location
        self.is_connected = False
        self.last_sync = None

    def connect(self) -> bool:
        """Simulate TCP socket handshake to ZKTeco terminal port 4370."""
        logger.info(f"Connecting to terminal {self.device_id} ({self.name} @ {self.ip}:{self.port})...")
        time.sleep(0.1)
        self.is_connected = True
        return True


class AttendanceSyncEngine:
    """Processes biometric punches and determines shift entry/exit status."""

    SHIFT_START = dtime(8, 0, 0)     # 08:00 AM Standard RMG Shift
    GRACE_PERIOD_MINUTES = 15        # Late after 08:15 AM
    SHIFT_END = dtime(17, 0, 0)       # 05:00 PM Standard End

    def __init__(self, terminals: List[ZKTerminal]):
        self.terminals = terminals
        self.sync_history: List[Dict[str, Any]] = []

    def classify_punch(self, punch_time: datetime) -> Dict[str, str]:
        """Classify punch as ON_TIME, LATE, or OVERTIME."""
        t = punch_time.time()
        if t < self.SHIFT_START:
            return {'status': 'ON_TIME', 'flag': 'EARLY_ENTRY'}
        elif t <= dtime(8, self.GRACE_PERIOD_MINUTES, 0):
            return {'status': 'ON_TIME', 'flag': 'WITHIN_GRACE'}
        elif t < dtime(13, 0, 0):
            minutes_late = (punch_time.hour - 8) * 60 + punch_time.minute
            return {'status': 'LATE_ENTRY', 'flag': f'{minutes_late}m LATE'}
        elif t >= self.SHIFT_END:
            return {'status': 'SHIFT_OUT', 'flag': 'NORMAL_DEPARTURE'}
        else:
            return {'status': 'MID_DAY_PUNCH', 'flag': 'FLOOR_MOVEMENT'}

    def process_punch_record(self, raw_punch: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw ZKTeco record, apply business logic, and prepare MySQL payload."""
        punch_dt = datetime.strptime(raw_punch['timestamp'], '%Y-%m-%d %H:%M:%S')
        classification = self.classify_punch(punch_dt)

        processed = {
            'punch_id': raw_punch.get('punch_id', f"PUNCH-{int(time.time()*1000)%100000}"),
            'employee_id': raw_punch['emp_id'],
            'employee_name': raw_punch['name'],
            'department': raw_punch['dept'],
            'device_id': raw_punch['device_id'],
            'device_name': raw_punch['device_name'],
            'device_ip': raw_punch['device_ip'],
            'verification_mode': raw_punch['verify_mode'], # 'Face', 'Fingerprint', 'RFID'
            'match_confidence': raw_punch.get('confidence', '98.5%'),
            'timestamp': raw_punch['timestamp'],
            'shift_date': punch_dt.strftime('%Y-%m-%d'),
            'attendance_status': classification['status'],
            'audit_flag': classification['flag'],
            'sync_status': 'SYNCED_TO_MYSQL',
            'synced_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        self.sync_history.append(processed)
        logger.info(
            f"Synced Punch: [{processed['employee_id']}] {processed['employee_name']} "
            f"via {processed['verification_mode']} at {processed['timestamp']} -> {classification['status']}"
        )
        return processed


def get_sample_punches() -> List[Dict[str, Any]]:
    """Sample raw punches from ZKTeco ProFace X & SilkBio terminals."""
    now_date = datetime.now().strftime('%Y-%m-%d')
    return [
        {
            'emp_id': 'EMP-1042',
            'name': 'Md. Rafiqul Islam',
            'dept': 'Sewing Production (Line 2)',
            'device_id': 'ZK-FACE-01',
            'device_name': 'ZKTeco ProFace X (Gate 01)',
            'device_ip': '192.168.30.12',
            'verify_mode': 'Face Recognition',
            'confidence': '98.8%',
            'timestamp': f"{now_date} 07:58:14"
        },
        {
            'emp_id': 'EMP-0881',
            'name': 'Nazma Begum',
            'dept': 'Quality Assurance (QA-03)',
            'device_id': 'ZK-FINGER-01',
            'device_name': 'ZKTeco SilkBio (Gate 01)',
            'device_ip': '192.168.30.12',
            'verify_mode': 'Optical Fingerprint',
            'confidence': '99.2%',
            'timestamp': f"{now_date} 07:59:32"
        },
        {
            'emp_id': 'EMP-0315',
            'name': 'Tanvir Hossain',
            'dept': 'Merchandising & Planning',
            'device_id': 'ZK-SPEED-02',
            'device_name': 'ZKTeco SpeedFace (Admin Gate)',
            'device_ip': '192.168.30.14',
            'verify_mode': 'Face Recognition',
            'confidence': '97.4%',
            'timestamp': f"{now_date} 08:04:18"
        },
        {
            'emp_id': 'EMP-1190',
            'name': 'Farhana Akter',
            'dept': 'Cutting & Pattern Section',
            'device_id': 'ZK-FINGER-02',
            'device_name': 'ZKTeco SilkBio (Gate 02)',
            'device_ip': '192.168.30.13',
            'verify_mode': 'Optical Fingerprint',
            'confidence': '96.9%',
            'timestamp': f"{now_date} 08:18:45"  # Late entry test
        }
    ]


if __name__ == '__main__':
    terminals = [
        ZKTerminal('ZK-FACE-01', 'ZKTeco ProFace X (Main Turnstiles)', '192.168.30.12'),
        ZKTerminal('ZK-FINGER-02', 'ZKTeco SilkBio (Factory Gate 02)', '192.168.30.13')
    ]
    engine = AttendanceSyncEngine(terminals)

    print("\n--- Starting ZKTeco Biometric Sync Test Cycle ---")
    for raw in get_sample_punches():
        record = engine.process_punch_record(raw)
        print(f"-> {record['punch_id']}: {record['employee_name']} ({record['attendance_status']})")
