"""
FILE: crud.py
SQLite CRUD for PMRS (CSV export only; JSON removed).
"""
import sqlite3
from typing import List, Dict, Any, Optional


class PatientCRUD:
    def __init__(self, db_path: str = 'patients.db'):
        self.db_path = db_path
        self._ensure_table()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_table(self):
        """
        Create the patients table with required columns if it doesn't exist.
        If some columns are missing from an older schema, ALTER TABLE to add them.
        Note: we DO NOT keep 'age' as a DB column anymore.
        """
        conn = self._connect()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                middle_name TEXT,
                last_name TEXT,
                name_ext TEXT,
                birthdate TEXT,
                gender TEXT,
                contact TEXT,
                address TEXT,
                diagnosis TEXT,
                notes TEXT
            )
        ''')
        conn.commit()

        # Ensure backward-compatible columns exist (add missing ones)
        required_columns = {
            'first_name': 'TEXT',
            'middle_name': 'TEXT',
            'last_name': 'TEXT',
            'name_ext': 'TEXT',
            'birthdate': 'TEXT',
            'gender': 'TEXT',
            'contact': 'TEXT',
            'address': 'TEXT',
            'diagnosis': 'TEXT',
            'notes': 'TEXT'
        }

        c.execute("PRAGMA table_info(patients)")
        existing_info = c.fetchall()  # rows: (cid, name, type, notnull, dflt_value, pk)
        existing_cols = {row[1] for row in existing_info}

        for col, coltype in required_columns.items():
            if col not in existing_cols:
                try:
                    c.execute(f'ALTER TABLE patients ADD COLUMN {col} {coltype}')
                    conn.commit()
                except Exception:
                    # ignore ALTER TABLE errors on odd sqlite builds
                    pass

        conn.close()

    # --------------------------
    # Duplicate Checker
    # --------------------------
    def is_duplicate(self, first: Optional[str], middle: Optional[str], last: Optional[str], birthdate: Optional[str]) -> bool:
        conn = self._connect()
        c = conn.cursor()
        c.execute('''
            SELECT COUNT(*) FROM patients
            WHERE first_name=? AND middle_name=? AND last_name=? AND birthdate=?
        ''', (first, middle, last, birthdate))
        count = c.fetchone()[0]
        conn.close()
        return count > 0

    def is_duplicate_except_id(self, first: Optional[str], middle: Optional[str], last: Optional[str], birthdate: Optional[str], exclude_id: int) -> bool:
        conn = self._connect()
        c = conn.cursor()
        c.execute('''
            SELECT COUNT(*) FROM patients
            WHERE first_name=? AND middle_name=? AND last_name=? AND birthdate=? AND id<>?
        ''', (first, middle, last, birthdate, exclude_id))
        count = c.fetchone()[0]
        conn.close()
        return count > 0

    # --------------------------
    # ADD PATIENT
    # --------------------------
    def add_patient(self, patient: Dict[str, Any]) -> int:
        """
        Returns:
            -1 : duplicate detected
            >0 : inserted row id
        """
        if self.is_duplicate(
            patient.get('first_name'),
            patient.get('middle_name'),
            patient.get('last_name'),
            patient.get('birthdate')
        ):
            return -1  # duplicate

        conn = self._connect()
        c = conn.cursor()
        c.execute('''
            INSERT INTO patients
            (first_name, middle_name, last_name, name_ext, birthdate, gender, contact, address, diagnosis, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient.get('first_name'),
            patient.get('middle_name'),
            patient.get('last_name'),
            patient.get('name_ext'),
            patient.get('birthdate'),
            patient.get('gender'),
            patient.get('contact'),
            patient.get('address'),
            patient.get('diagnosis'),
            patient.get('notes')
        ))
        conn.commit()
        pid = c.lastrowid
        conn.close()
        return pid

    # --------------------------
    # GET
    # --------------------------
    def get_patient(self, patient_id: int) -> Dict[str, Any]:
        conn = self._connect()
        c = conn.cursor()
        c.execute('''
            SELECT id, first_name, middle_name, last_name, name_ext, birthdate, gender, contact, address, diagnosis, notes
            FROM patients WHERE id = ?
        ''', (patient_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return {}
        keys = ['id', 'first_name', 'middle_name', 'last_name', 'name_ext', 'birthdate', 'gender', 'contact', 'address', 'diagnosis', 'notes']
        return dict(zip(keys, row))

    # --------------------------
    # UPDATE
    # --------------------------
    def update_patient(self, patient_id: int, data: Dict[str, Any]) -> int:
        """
        Returns:
            -1 : duplicate would result (another record with same name parts + birthdate)
             0 : no rows changed (maybe id not found)
             1 : updated successfully (rowcount > 0)
        """
        if self.is_duplicate_except_id(
            data.get('first_name'),
            data.get('middle_name'),
            data.get('last_name'),
            data.get('birthdate'),
            patient_id
        ):
            return -1

        conn = self._connect()
        c = conn.cursor()
        c.execute('''
            UPDATE patients SET
                first_name=?, middle_name=?, last_name=?, name_ext=?, birthdate=?, gender=?, contact=?, address=?, diagnosis=?, notes=?
            WHERE id=?
        ''', (
            data.get('first_name'),
            data.get('middle_name'),
            data.get('last_name'),
            data.get('name_ext'),
            data.get('birthdate'),
            data.get('gender'),
            data.get('contact'),
            data.get('address'),
            data.get('diagnosis'),
            data.get('notes'),
            patient_id
        ))
        conn.commit()
        changed = c.rowcount
        conn.close()
        return 1 if changed > 0 else 0

    # --------------------------
    # DELETE
    # --------------------------
    def delete_patient(self, patient_id: int) -> bool:
        conn = self._connect()
        c = conn.cursor()
        c.execute('DELETE FROM patients WHERE id=?', (patient_id,))
        conn.commit()
        changed = c.rowcount
        conn.close()
        return changed > 0

    # --------------------------
    # LIST
    # --------------------------
    def list_patients(self) -> List[Dict[str, Any]]:
        conn = self._connect()
        c = conn.cursor()
        c.execute('''
            SELECT id, first_name, middle_name, last_name, name_ext, birthdate, gender, contact, address, diagnosis, notes
            FROM patients ORDER BY id DESC
        ''')
        rows = c.fetchall()
        conn.close()
        keys = ['id', 'first_name', 'middle_name', 'last_name', 'name_ext', 'birthdate', 'gender', 'contact', 'address', 'diagnosis', 'notes']
        return [dict(zip(keys, r)) for r in rows]

    # --------------------------
    # EXPORT CSV (only)
    # --------------------------
    def export_csv(self, path: str = 'patients_export.csv') -> None:
        import csv
        data = self.list_patients()
        if not data:
            # create an empty file with headers
            keys = ['id', 'first_name', 'middle_name', 'last_name', 'name_ext', 'birthdate', 'gender', 'contact', 'address', 'diagnosis', 'notes']
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
            return
        keys = list(data[0].keys())
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
