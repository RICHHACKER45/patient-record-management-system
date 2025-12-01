# ----------------------------
# FILE: crud.py
# Patient Management CRUD for Patients, Address, Diagnosis
# ----------------------------
import sqlite3
import csv
from typing import List, Dict, Any
from datetime import datetime

DB_PATH = 'patients.db'

class PatientCRUD:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._create_tables()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        conn = self._connect()
        c = conn.cursor()

        # Address Table
        c.execute('''
        CREATE TABLE IF NOT EXISTS address (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            house_no TEXT,
            street TEXT,
            barangay TEXT,
            city TEXT,
            province TEXT,
            postal_code TEXT
        )
        ''')

        # Diagnosis Table
        c.execute('''
        CREATE TABLE IF NOT EXISTS diagnosis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
        ''')

        # Patients Table with cascades
        c.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            last_name TEXT NOT NULL,
            suffix TEXT,
            sex TEXT,
            birthdate TEXT,
            contact_no TEXT,
            height_cm REAL,
            weight_kg REAL,
            diagnosis_id INTEGER,
            address_id INTEGER,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(diagnosis_id) REFERENCES diagnosis(id)
                ON UPDATE CASCADE
                ON DELETE SET NULL,
            FOREIGN KEY(address_id) REFERENCES address(id)
                ON UPDATE CASCADE
                ON DELETE SET NULL
        )
        ''')
        conn.commit()
        conn.close()

    # ----------------------------
    # Address CRUD
    # ----------------------------
    def add_address(self, addr: Dict[str, Any]) -> int:
        conn = self._connect()
        c = conn.cursor()
        c.execute('''
        INSERT INTO address (house_no, street, barangay, city, province, postal_code)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            addr.get('house_no'),
            addr.get('street'),
            addr.get('barangay'),
            addr.get('city'),
            addr.get('province'),
            addr.get('postal_code')
        ))
        conn.commit()
        aid = c.lastrowid
        conn.close()
        return aid

    def list_addresses(self) -> List[Dict[str, Any]]:
        conn = self._connect()
        c = conn.cursor()
        c.execute('SELECT * FROM address')
        rows = c.fetchall()
        conn.close()
        keys = ['id','house_no','street','barangay','city','province','postal_code']
        return [dict(zip(keys, r)) for r in rows]

    # ----------------------------
    # Diagnosis CRUD
    # ----------------------------
    def add_diagnosis(self, name: str) -> int:
        conn = self._connect()
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO diagnosis (name) VALUES (?)', (name,))
        conn.commit()
        diag_id = c.lastrowid
        if diag_id == 0:  # already exists, fetch id
            c.execute('SELECT id FROM diagnosis WHERE name=?', (name,))
            diag_id = c.fetchone()[0]
        conn.close()
        return diag_id

    def list_diagnoses(self) -> List[Dict[str, Any]]:
        conn = self._connect()
        c = conn.cursor()
        c.execute('SELECT * FROM diagnosis')
        rows = c.fetchall()
        conn.close()
        keys = ['id','name']
        return [dict(zip(keys, r)) for r in rows]

    # ----------------------------
    # Patient CRUD
    # ----------------------------
    def add_patient(self, p: Dict[str, Any]) -> int:
        conn = self._connect()
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute('''
        INSERT INTO patients (
            first_name, middle_name, last_name, suffix, sex, birthdate,
            contact_no, height_cm, weight_kg, diagnosis_id, address_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            p.get('first_name'),
            p.get('middle_name'),
            p.get('last_name'),
            p.get('suffix'),
            p.get('sex'),
            p.get('birthdate'),
            p.get('contact_no'),
            p.get('height_cm'),
            p.get('weight_kg'),
            p.get('diagnosis_id'),
            p.get('address_id'),
            now,
            now
        ))
        conn.commit()
        pid = c.lastrowid
        conn.close()
        return pid

    def get_patient(self, patient_id: int) -> Dict[str, Any]:
        conn = self._connect()
        c = conn.cursor()
        c.execute('SELECT * FROM patients WHERE id=?', (patient_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return {}
        keys = ['id','first_name','middle_name','last_name','suffix','sex','birthdate',
                'contact_no','height_cm','weight_kg','diagnosis_id','address_id','created_at','updated_at']
        return dict(zip(keys, row))

    def update_patient(self, patient_id: int, p: Dict[str, Any]) -> bool:
        conn = self._connect()
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute('''
        UPDATE patients
        SET first_name=?, middle_name=?, last_name=?, suffix=?, sex=?, birthdate=?,
            contact_no=?, height_cm=?, weight_kg=?, diagnosis_id=?, address_id=?, updated_at=?
        WHERE id=?
        ''', (
            p.get('first_name'),
            p.get('middle_name'),
            p.get('last_name'),
            p.get('suffix'),
            p.get('sex'),
            p.get('birthdate'),
            p.get('contact_no'),
            p.get('height_cm'),
            p.get('weight_kg'),
            p.get('diagnosis_id'),
            p.get('address_id'),
            now,
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
        c.execute('SELECT * FROM patients ORDER BY created_at DESC')
        rows = c.fetchall()
        conn.close()
        keys = ['id','first_name','middle_name','last_name','suffix','sex','birthdate',
                'contact_no','height_cm','weight_kg','diagnosis_id','address_id','created_at','updated_at']
        return [dict(zip(keys, r)) for r in rows]

    # ----------------------------
    # CSV Export
    # ----------------------------
    def export_patients_csv(self, path='patients.csv'):
        data = self.list_patients()
        if not data:
            return
        keys = list(data[0].keys())
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)

