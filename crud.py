# crud.py
"""
Robust SQLite helper for PMRS.
- Uses per-operation connections (avoids 'database is locked')
- Returns rows in formats the GUI expects:
    * get_patients() -> list[tuple]
    * get_patient(id) -> dict (single patient record) or None
- add_patient accepts dict or keyword args
- Sets PRAGMA foreign_keys = ON for each connection
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

DB_NAME = "pmrs.db"


class Database:
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self._create_tables()

    # -------------------------
    # Internal helpers
    # -------------------------
    def _conn(self):
        # per-operation connection with a reasonable timeout
        conn = sqlite3.connect(self.db_name, timeout=30)
        return conn

    def _execute(self, query: str, params: tuple = (), fetch: bool = False, many: bool = False, row_factory=None):
        """
        Run a query inside a fresh connection. Returns rows if fetch=True.
        Use this for read-only or non-lastrowid needs.
        """
        with self._conn() as conn:
            if row_factory:
                conn.row_factory = row_factory
            conn.execute("PRAGMA foreign_keys = ON;")
            cur = conn.cursor()
            if many:
                cur.executemany(query, params)
            else:
                cur.execute(query, params)
            if fetch:
                return cur.fetchall()

    # -------------------------
    # Schema creation
    # -------------------------
    def _create_tables(self):
        # diagnoses
        self._execute("""
            CREATE TABLE IF NOT EXISTS diagnoses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
        """)
        # addresses
        self._execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                municipality TEXT NOT NULL,
                barangay TEXT NOT NULL,
                street TEXT,
                house_no TEXT,
                postal_code TEXT
            );
        """)
        # patients
        self._execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                middle_name TEXT,
                last_name TEXT NOT NULL,
                suffix TEXT,
                sex TEXT NOT NULL,
                birthdate TEXT NOT NULL,
                contact_no TEXT,
                height_cm REAL,
                weight_kg REAL,
                diagnosis_id INTEGER,
                address_id INTEGER,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(diagnosis_id) REFERENCES diagnoses(id)
                    ON UPDATE CASCADE ON DELETE SET NULL,
                FOREIGN KEY(address_id) REFERENCES addresses(id)
                    ON UPDATE CASCADE ON DELETE CASCADE
            );
        """)

    # -------------------------
    # Diagnosis CRUD
    # -------------------------
    def add_diagnosis(self, name: str) -> int:
        """Return id of diagnosis (create if missing)."""
        if not name:
            raise ValueError("Diagnosis name required")
        # insert-or-ignore then get id
        self._execute("INSERT OR IGNORE INTO diagnoses (name) VALUES (?)", (name.strip(),))
        rows = self._execute("SELECT id FROM diagnoses WHERE name = ?", (name.strip(),), fetch=True)
        return int(rows[0][0])

    def get_diagnoses(self) -> List[Tuple[int, str]]:
        rows = self._execute("SELECT id, name FROM diagnoses ORDER BY name", fetch=True)
        return rows or []

    # -------------------------
    # Address CRUD
    # -------------------------
    def get_or_create_address(self, municipality: str, barangay: str, street: Optional[str], house_no: Optional[str], postal_code: Optional[str]) -> int:
        """
        If an address with the exact fields exists, return its id.
        Otherwise insert and return new id.
        """
        if not municipality or not barangay:
            return None  # GUI may treat None as "no address"
        muni = municipality.strip()
        brgy = barangay.strip()
        st = street.strip() if street else None
        hn = house_no.strip() if house_no else None
        pc = postal_code.strip() if postal_code else None

        # try find existing
        rows = self._execute(
            """
            SELECT id FROM addresses
            WHERE municipality = ? AND barangay = ? AND COALESCE(street,'') = COALESCE(?, '') 
              AND COALESCE(house_no,'') = COALESCE(?, '') AND COALESCE(postal_code,'') = COALESCE(?, '')
            """,
            (muni, brgy, st, hn, pc),
            fetch=True
        )
        if rows:
            return int(rows[0][0])

        # insert and return lastrowid using same connection
        with self._conn() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO addresses (municipality, barangay, street, house_no, postal_code)
                VALUES (?, ?, ?, ?, ?)
                """,
                (muni, brgy, st, hn, pc)
            )
            conn.commit()
            return int(cur.lastrowid)

    def add_address(self, municipality: str, barangay: str, street: Optional[str], house_no: Optional[str], postal_code: Optional[str]) -> int:
        """
        Backwards-compatible add_address: insert address and return id.
        """
        return self.get_or_create_address(municipality, barangay, street, house_no, postal_code)

    def get_addresses(self) -> List[Tuple]:
        rows = self._execute("SELECT * FROM addresses ORDER BY municipality, barangay", fetch=True)
        return rows or []

    # -------------------------
    # Patient CRUD
    # -------------------------
    def add_patient(self, data: Optional[dict] = None, **kwargs) -> int:
        """
        Add patient. Accepts either a single dict in 'data' or keyword arguments.
        Returns inserted patient id.
        """
        if data is None:
            data = kwargs
        required = ["first_name", "last_name", "sex", "birthdate"]
        for f in required:
            if f not in data or not data[f]:
                raise ValueError(f"{f} is required")

        now = datetime.now().isoformat(" ", "seconds")
        first = data.get("first_name").strip()
        middle = data.get("middle_name").strip() if data.get("middle_name") else None
        last = data.get("last_name").strip()
        suffix = data.get("suffix").strip() if data.get("suffix") else None
        sex = data.get("sex")
        birthdate = data.get("birthdate")
        contact = data.get("contact_no").strip() if data.get("contact_no") else None
        height = data.get("height_cm")
        weight = data.get("weight_kg")
        diagnosis_id = data.get("diagnosis_id")
        address_id = data.get("address_id")
        notes = data.get("notes")

        # insert & return lastrowid using same connection
        with self._conn() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO patients (
                    first_name, middle_name, last_name, suffix,
                    sex, birthdate, contact_no,
                    height_cm, weight_kg,
                    diagnosis_id, address_id,
                    notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    first, middle, last, suffix,
                    sex, birthdate, contact,
                    height, weight,
                    diagnosis_id, address_id,
                    notes, now, now
                )
            )
            conn.commit()
            return int(cur.lastrowid)

    def get_patients(self) -> List[Tuple]:
        """
        Returns rows in order expected by GUI:
        (p.id, p.first_name, p.middle_name, p.last_name, p.suffix,
         p.sex, p.birthdate, p.contact_no,
         p.height_cm, p.weight_kg,
         d.name AS diagnosis,
         a.municipality, a.barangay, a.street, a.house_no, a.postal_code,
         p.notes, p.created_at, p.updated_at)
        """
        rows = self._execute("""
            SELECT
                p.id, p.first_name, p.middle_name, p.last_name, p.suffix,
                p.sex, p.birthdate, p.contact_no,
                p.height_cm, p.weight_kg,
                d.name AS diagnosis,
                a.municipality, a.barangay, a.street, a.house_no, a.postal_code,
                p.notes, p.created_at, p.updated_at
            FROM patients p
            LEFT JOIN diagnoses d ON p.diagnosis_id = d.id
            LEFT JOIN addresses a ON p.address_id = a.id
            ORDER BY p.id DESC;
        """, fetch=True)
        return rows or []

    def get_patient(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """Return a dict representing the patient row from patients table (not joined)."""
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            cur = conn.cursor()
            cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
            row = cur.fetchone()
            if not row:
                return None
            # convert sqlite3.Row to dict
            return {k: row[k] for k in row.keys()}

    def update_patient(self, patient_id: int, data: dict) -> None:
        if not patient_id:
            raise ValueError("patient_id is required")
        if "birthdate" not in data or not data["birthdate"]:
            raise ValueError("birthdate is required")

        now = datetime.now().isoformat(" ", "seconds")

        with self._conn() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE patients SET
                    first_name = ?, middle_name = ?, last_name = ?, suffix = ?,
                    sex = ?, birthdate = ?, contact_no = ?,
                    height_cm = ?, weight_kg = ?,
                    diagnosis_id = ?, address_id = ?,
                    notes = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    data.get("first_name").strip(),
                    data.get("middle_name").strip() if data.get("middle_name") else None,
                    data.get("last_name").strip(),
                    data.get("suffix").strip() if data.get("suffix") else None,
                    data.get("sex"),
                    data.get("birthdate"),
                    data.get("contact_no").strip() if data.get("contact_no") else None,
                    data.get("height_cm"),
                    data.get("weight_kg"),
                    data.get("diagnosis_id"),
                    data.get("address_id"),
                    data.get("notes"),
                    now,
                    patient_id
                )
            )
            conn.commit()

    def delete_patient(self, patient_id: int) -> None:
        self._execute("DELETE FROM patients WHERE id = ?", (patient_id,))

    # Helper close (not necessary with per-op connections, but kept for API compatibility)
    def close(self):
        # no persistent connection to close
        return
