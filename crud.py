"""
FILE: crud.py
Responsible for SQLite database CRUD and import/export (CSV/JSON).
Encapsulated in class PatientCRUD and all functions inside defs.
"""
import sqlite3
import json
from typing import List, Dict, Any

class PatientCRUD:
    def __init__(self, db_path: str = 'patients.db'):
        self.db_path = db_path
        self._ensure_table()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_table(self):
        conn = self._connect()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                age INTEGER,
                gender TEXT,
                contact TEXT,
                diagnosis TEXT,
                notes TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_patient(self, patient: Dict[str, Any]) -> int:
        conn = self._connect()
        c = conn.cursor()
        c.execute('''
            INSERT INTO patients (first_name, last_name, age, gender, contact, diagnosis, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient.get('first_name'),
            patient.get('last_name'),
            patient.get('age'),
            patient.get('gender'),
            patient.get('contact'),
            patient.get('diagnosis'),
            patient.get('notes')
        ))
        conn.commit()
        pid = c.lastrowid
        conn.close()
        return pid

    def get_patient(self, patient_id: int) -> Dict[str, Any]:
        conn = self._connect()
        c = conn.cursor()
        c.execute('SELECT * FROM patients WHERE id = ?', (patient_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return {}
        keys = ['id','first_name','last_name','age','gender','contact','diagnosis','notes']
        return dict(zip(keys, row))

    def update_patient(self, patient_id: int, data: Dict[str, Any]) -> bool:
        conn = self._connect()
        c = conn.cursor()
        c.execute('''
            UPDATE patients SET first_name=?, last_name=?, age=?, gender=?, contact=?, diagnosis=?, notes=?
            WHERE id=?
        ''', (
            data.get('first_name'),
            data.get('last_name'),
            data.get('age'),
            data.get('gender'),
            data.get('contact'),
            data.get('diagnosis'),
            data.get('notes'),
            patient_id
        ))
        conn.commit()
        changed = c.rowcount
        conn.close()
        return changed > 0

    def delete_patient(self, patient_id: int) -> bool:
        conn = self._connect()
        c = conn.cursor()
        c.execute('DELETE FROM patients WHERE id=?', (patient_id,))
        conn.commit()
        changed = c.rowcount
        conn.close()
        return changed > 0

    def list_patients(self) -> List[Dict[str, Any]]:
        conn = self._connect()
        c = conn.cursor()
        c.execute('SELECT * FROM patients ORDER BY id DESC')
        rows = c.fetchall()
        conn.close()
        keys = ['id','first_name','last_name','age','gender','contact','diagnosis','notes']
        return [dict(zip(keys, r)) for r in rows]

    def export_json(self, path: str = 'patients_export.json') -> None:
        data = self.list_patients()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_json(self, path: str) -> int:
        with open(path, 'r', encoding='utf-8') as f:
            arr = json.load(f)
        count = 0
        for p in arr:
            self.add_patient(p)
            count += 1
        return count

    def export_csv(self, path: str = 'patients_export.csv') -> None:
        import csv
        data = self.list_patients()
        if not data:
            return
        keys = list(data[0].keys())
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)

