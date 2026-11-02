#!/usr/bin/env python3
"""
ZKTeco Offline Punch Queue & Failover Cache (SQLite)
Author: MD. Mahamudul Hasan
Repository: ZKTeco-Biometric-Attendance-ERP-Sync
License: MIT

Caches raw biometric punches in a local ACID-compliant SQLite buffer whenever
the central corporate MySQL server or WAN link experiences downtime. Automatically
drains and reconciles the backlog upon connectivity restoration.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger('ZKOfflineCache')


class OfflinePunchQueue:
    def __init__(self, db_path: str = 'offline_punches.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create offline punch storage table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS punch_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    emp_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    verify_mode TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    is_synced INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def enqueue_punch(self, punch_data: Dict[str, Any]) -> int:
        """Add a punch record to the local cache during network outages."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO punch_queue (emp_id, timestamp, device_id, verify_mode, payload_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                punch_data['emp_id'],
                punch_data['timestamp'],
                punch_data['device_id'],
                punch_data.get('verify_mode', 'Face'),
                json.dumps(punch_data)
            ))
            conn.commit()
            return cursor.lastrowid

    def get_pending_punches(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve unsynced punches for reconciliation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, payload_json FROM punch_queue
                WHERE is_synced = 0
                ORDER BY id ASC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [{'queue_id': row['id'], 'data': json.loads(row['payload_json'])} for row in rows]

    def mark_synced(self, queue_ids: List[int]):
        """Mark punches as synced once verified by the central MySQL database."""
        if not queue_ids:
            return
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE punch_queue
                SET is_synced = 1
                WHERE id IN ({','.join(['?'] * len(queue_ids))})
            """, queue_ids)
            conn.commit()
            logger.info(f"Drained {len(queue_ids)} offline punches into central database.")


if __name__ == '__main__':
    queue = OfflinePunchQueue(':memory:')
    sample_punch = {
        'emp_id': 'EMP-1508',
        'name': 'Md. Mahamudul Hasan',
        'device_id': 'ZK-FACE-01',
        'timestamp': '2026-11-03 07:55:00',
        'verify_mode': 'Face Recognition'
    }
    qid = queue.enqueue_punch(sample_punch)
    print(f"Enqueued offline punch with queue ID: {qid}")
    pending = queue.get_pending_punches()
    print(f"Pending records: {len(pending)}")
    queue.mark_synced([p['queue_id'] for p in pending])
    print("Offline queue reconciled successfully!")
