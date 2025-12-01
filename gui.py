# gui.py
"""
Refactored Modern PMRS GUI (Nueva Ecija scope)
- Same features & behavior as your original GUI
- Loads municipality->barangay from address_data.json (utf-8)
- Dark theme ("darkly") and outline button styles preserved
- Cleaner, data-driven construction and helper functions
"""

import json
import os
import csv
from datetime import date, datetime
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# Local application modules (must exist)
from crud import Database      # your updated crud.py Database class
from data_utils import db_to_dataframe
from graph_report import generate_pdf_report

# ---------- Config ----------
THEME = "darkly"
DEFAULT_ADDRESS_JSON = os.path.join(os.path.dirname(__file__), "address_data.json")
COMMON_DIAGNOSES = ["Asthma", "Hypertension", "Diabetes", "Flu", "Common Cold"]

# ---------- Utilities ----------
def load_address_data(path: str | None = None) -> dict:
    """Load municipality->barangay mapping from JSON (utf-8). Returns {} if any issue."""
    if path is None:
        path = DEFAULT_ADDRESS_JSON
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cleaned = {}
        for muni, brgys in (data or {}).items():
            if isinstance(brgys, list):
                cleaned[muni.strip()] = [str(b).strip() for b in brgys if str(b).strip()]
        return cleaned
    except FileNotFoundError:
        print(f"[WARN] address JSON not found at {path}. Using empty address_data.")
        return {}
    except Exception as e:
        print(f"[WARN] failed to load address JSON: {e}")
        return {}

def get_or_create_diagnosis(db: Database, name: str):
    """Return diagnosis id for name; create if not exists."""
    if not name:
        return None
    rows = db.get_diagnoses()
    for r in rows:
        if r[1].strip().lower() == name.strip().lower():
            return r[0]
    db.add_diagnosis(name.strip())
    rows = db.get_diagnoses()
    for r in rows:
        if r[1].strip().lower() == name.strip().lower():
            return r[0]
    return None

# ---------- PMRS App ----------
class PMRSApp:
    def __init__(self, root, address_data: dict):
        self.root = root
        self.root.title("PMRS — Patient Management (Nueva Ecija)")
        # geometry is controlled by start_app; default not forced here
        self.style = tb.Style(theme=THEME)
        self.db = Database()
        self.address_data = address_data or {}

        # create variables container
        self._vars = {}
        self._build_ui()
        self._refresh_list()

    # ---------------- UI helpers ----------------
    def _mk_text(self, parent, width=40):
        t = tb.Entry(parent)
        return t

    def _label(self, parent, text, row, sticky="e"):
        tb.Label(parent, text=text).grid(row=row, column=0, sticky=sticky, padx=6, pady=2)

    def _add_entry(self, parent, key, row, **kwargs):
        self._label(parent, f"{key}: ", row)
        v = tk.StringVar()
        e = tb.Entry(parent, textvariable=v, **kwargs)
        e.grid(row=row, column=1, sticky="we", padx=6, pady=2)
        self._vars[key] = v
        return e

    def _add_combobox(self, parent, key, values, row, state="readonly", width=None):
        self._label(parent, f"{key}: ", row)
        v = tk.StringVar()
        cb = tb.Combobox(parent, values=values, textvariable=v, state=state, width=width)
        cb.grid(row=row, column=1, sticky="we", padx=6, pady=2)
        self._vars[key] = v
        return cb

    def _add_radiobuttons(self, parent, key, options, row):
        self._label(parent, f"{key}: ", row, sticky="ne")
        frame = tb.Frame(parent)
        frame.grid(row=row, column=1, sticky="w", padx=6, pady=2)
        v = tk.StringVar(value=options[0][0] if options else "")
        for text, value in options:
            tb.Radiobutton(frame, text=text, variable=v, value=value).pack(side=LEFT, padx=(0,8))
        self._vars[key] = v
        return frame

    # ---------------- Build UI ----------------
    def _build_ui(self):
        main = tb.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        # LEFT: Form
        form = tb.Labelframe(main, text="Patient Form", padding=12)
        form.pack(side=LEFT, fill="y", padx=(0, 10), anchor="n")
        form.grid_columnconfigure(0, weight=0)
        form.grid_columnconfigure(1, weight=1)

        row = 0
        # Basic text fields
        self.first_entry = self._add_entry(form, "First name", row); row += 1
        self.middle_entry = self._add_entry(form, "Middle name", row); row += 1
        self.last_entry = self._add_entry(form, "Last name", row); row += 1

        # Suffix combobox
        self._add_combobox(form, "Suffix", ["", "Jr", "Sr", "I", "II", "III"], row, state="readonly"); row += 1

        # Birthdate grouped
        self._label(form, "Birthdate: ", row)
        bd_frame = tb.Frame(form)
        bd_frame.grid(row=row, column=1, sticky="w", padx=6, pady=2)
        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        self._vars["BD_month"] = tk.StringVar()
        self._vars["BD_day"] = tk.StringVar()
        self._vars["BD_year"] = tk.StringVar()
        tb.Combobox(bd_frame, values=months, textvariable=self._vars["BD_month"], width=8).pack(side=LEFT, padx=(0,6))
        tb.Combobox(bd_frame, values=[str(i) for i in range(1,32)], textvariable=self._vars["BD_day"], width=5).pack(side=LEFT, padx=(0,6))
        current_year = date.today().year
        tb.Combobox(bd_frame, values=[str(y) for y in range(current_year, current_year-120, -1)], textvariable=self._vars["BD_year"], width=7).pack(side=LEFT)
        row += 1

        self._add_entry(form, "Contact No.", row); row += 1

        # Sex radio
        self._vars["Sex"] = tk.StringVar(value="Male")
        self._label(form, "Sex: ", row)
        sex_frame = tb.Frame(form)
        sex_frame.grid(row=row, column=1, sticky="w", padx=6, pady=2)
        tb.Radiobutton(sex_frame, text="Male", variable=self._vars["Sex"], value="Male").pack(side=LEFT, padx=(0,6))
        tb.Radiobutton(sex_frame, text="Female", variable=self._vars["Sex"], value="Female").pack(side=LEFT)
        row += 1

        self._add_entry(form, "Height (cm)", row); row += 1
        self._add_entry(form, "Weight (kg)", row); row += 1

        # Diagnosis: common vs other
        self._label(form, "Diagnosis: ", row)
        diag_frame = tb.Frame(form)
        diag_frame.grid(row=row, column=1, sticky="we", padx=6, pady=2)
        self._vars["Diagnosis_choice"] = tk.StringVar(value="common")
        tb.Radiobutton(diag_frame, text="Common", variable=self._vars["Diagnosis_choice"], value="common", command=self._on_diag_choice).pack(side=LEFT, padx=(0,8))
        tb.Radiobutton(diag_frame, text="Other", variable=self._vars["Diagnosis_choice"], value="other", command=self._on_diag_choice).pack(side=LEFT)
        row += 1

        # Common diagnosis combobox and other entry
        self.common_diag_cb = self._add_combobox(form, "Common diagnosis", COMMON_DIAGNOSES, row, state="readonly"); row += 1
        self.other_diag_entry_widget = tb.Entry(form, state="disabled")
        self._label(form, "Other diagnosis: ", row)
        self.other_diag_entry_widget.grid(row=row, column=1, sticky="we", padx=6, pady=2)
        self._vars["Other diagnosis"] = tk.StringVar()
        self.other_diag_entry_widget.config(textvariable=self._vars["Other diagnosis"])
        row += 1

        # Notes (multiline)
        self._label(form, "Notes: ", row, sticky="ne")
        self.notes_text = tb.Text(form, width=48, height=6, wrap="word")
        self.notes_text.grid(row=row, column=1, sticky="we", padx=6, pady=(6,2))
        row += 1

        tb.Separator(form).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(12,8))
        row += 1

        # Address fields
        # Municipality combobox (values come from loaded address_data)
        self._vars["Municipality/City"] = tk.StringVar()
        self._label(form, "Municipality/City: ", row)
        self.muni_cb = tb.Combobox(form, textvariable=self._vars["Municipality/City"], values=list(self.address_data.keys()), state="readonly")
        self.muni_cb.grid(row=row, column=1, sticky="we", padx=6, pady=2)
        self.muni_cb.bind("<<ComboboxSelected>>", self._on_muni_selected)
        row += 1

        # Barangay combobox
        self._vars["Barangay"] = tk.StringVar()
        self._label(form, "Barangay: ", row)
        self.barangay_cb = tb.Combobox(form, textvariable=self._vars["Barangay"], values=[], state="disabled")
        self.barangay_cb.grid(row=row, column=1, sticky="we", padx=6, pady=2)
        row += 1

        self._add_entry(form, "House/Unit No.", row); row += 1
        self._add_entry(form, "Street", row); row += 1
        self._add_entry(form, "Postal Code", row); row += 1

        # Actions (buttons)
        actions = tb.Frame(form)
        actions.grid(row=row, column=0, columnspan=2, pady=(12,0))
        tb.Button(actions, text="Add Patient", bootstyle="success-outline", command=self.add_patient).grid(row=0, column=0, padx=6, pady=6)
        tb.Button(actions, text="Update", bootstyle="primary-outline", command=self.update_patient).grid(row=0, column=1, padx=6, pady=6)
        tb.Button(actions, text="Delete", bootstyle="danger-outline", command=self.delete_patient).grid(row=0, column=2, padx=6, pady=6)
        tb.Button(actions, text="Clear", bootstyle="secondary-outline", command=self.clear_form).grid(row=0, column=3, padx=6, pady=6)
        tb.Button(actions, text="Export CSV", bootstyle="info-outline", command=self.export_csv).grid(row=0, column=4, padx=6, pady=6)
        tb.Button(actions, text="Generate PDF Report", bootstyle="warning-outline", command=self.generate_report).grid(row=0, column=5, padx=6, pady=6)

        # RIGHT: Patients list
        list_frame = tb.Labelframe(main, text="Patients", padding=10)
        list_frame.pack(side=RIGHT, fill="both", expand=True)
        cols = ("id","first_name","last_name","birthdate","age","sex","contact_no","municipality","barangay","diagnosis")
        self.tree = tb.Treeview(list_frame, columns=cols, show="headings", bootstyle="info")
        for c in cols:
            self.tree.heading(c, text=c.replace("_"," ").title())
            self.tree.column(c, width=110 if c!="id" else 50, anchor=CENTER)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def _on_diag_choice(self):
        choice = self._vars["Diagnosis_choice"].get()
        if choice == "common":
            self.common_diag_cb.configure(state="readonly")
            self.other_diag_entry_widget.configure(state="disabled")
        else:
            self.common_diag_cb.configure(state="disabled")
            self.other_diag_entry_widget.configure(state="normal")

    def _on_muni_selected(self, event=None):
        muni = self._vars["Municipality/City"].get()
        barangays = self.address_data.get(muni, [])
        if barangays:
            self.barangay_cb.configure(values=barangays, state="readonly")
        else:
            self.barangay_cb.configure(values=[], state="disabled")
        self._vars["Barangay"].set("")

    # ---------------- form helpers ----------------
    def _get_birthdate_iso(self):
        m = self._vars["BD_month"].get(); d = self._vars["BD_day"].get(); y = self._vars["BD_year"].get()
        if not (m and d and y):
            return None
        months_map = {"Jan":"01","Feb":"02","Mar":"03","Apr":"04","May":"05","Jun":"06",
                      "Jul":"07","Aug":"08","Sep":"09","Oct":"10","Nov":"11","Dec":"12"}
        mm = months_map.get(m, "01")
        dd = d.zfill(2)
        return f"{y}-{mm}-{dd}"

    def _calculate_age(self, birth_iso):
        if not birth_iso: return ""
        y, m, d = map(int, birth_iso.split("-"))
        today = date.today()
        return today.year - y - ((today.month, today.day) < (m, d))

    def clear_form(self):
        # clear all Tk vars and text
        for k, v in list(self._vars.items()):
            try:
                v.set("")
            except Exception:
                pass
        self._vars["Sex"].set("Male")
        self._vars["Diagnosis_choice"].set("common")
        self._on_diag_choice()
        self.notes_text.delete("1.0", "end")
        self.barangay_cb.configure(values=[], state="disabled")
        # unselect tree
        for sel in self.tree.selection():
            self.tree.selection_remove(sel)

    def _collect_patient_from_form(self):
        birth_iso = self._get_birthdate_iso()
        # choose diagnosis
        if self._vars["Diagnosis_choice"].get() == "common":
            diag_name = self._vars.get("Common diagnosis", tk.StringVar()).get().strip()
        else:
            diag_name = self._vars.get("Other diagnosis", tk.StringVar()).get().strip()
        diag_id = get_or_create_diagnosis(self.db, diag_name) if diag_name else None

        # address
        muni = self._vars.get("Municipality/City", tk.StringVar()).get().strip()
        brgy = self._vars.get("Barangay", tk.StringVar()).get().strip()
        house_no = self._vars.get("House/Unit No.", tk.StringVar()).get().strip()
        street = self._vars.get("Street", tk.StringVar()).get().strip()
        postal = self._vars.get("Postal Code", tk.StringVar()).get().strip()
        addr_id = self.db.get_or_create_address(muni, brgy, street, house_no, postal)

        # numeric conversion safe
        def to_float_key(k):
            val = self._vars.get(k, tk.StringVar()).get().strip()
            return float(val) if val else None

        patient = {
            "first_name": self._vars.get("First name", tk.StringVar()).get().strip(),
            "middle_name": self._vars.get("Middle name", tk.StringVar()).get().strip(),
            "last_name": self._vars.get("Last name", tk.StringVar()).get().strip(),
            "suffix": self._vars.get("Suffix", tk.StringVar()).get().strip(),
            "sex": self._vars.get("Sex", tk.StringVar()).get(),
            "birthdate": birth_iso,
            "contact_no": self._vars.get("Contact No.", tk.StringVar()).get().strip(),
            "height_cm": to_float_key("Height (cm)"),
            "weight_kg": to_float_key("Weight (kg)"),
            "diagnosis_id": diag_id,
            "address_id": addr_id,
            "notes": self.notes_text.get("1.0","end").strip()
        }
        return patient

    # ---------------- CRUD callbacks ----------------
    def add_patient(self):
    """GUI callback: collect form data, validate and call Database.add_patient."""
    try:
        # Collect form data
        patient = self._collect_patient_from_form()
    except ValueError as ve:
        # _collect_patient_from_form already throws a missing field error
        messagebox.showwarning("Validation", str(ve))
        return

    # Final GUI-side validation (DB also checks)
    required = ["first_name", "last_name", "sex", "birthdate"]
    for field in required:
        if not patient.get(field):
            messagebox.showwarning("Validation", f"{field.replace('_', ' ').title()} is required.")
            return

    try:
        # Attempt to insert into database (duplicate-safe)
        new_id = self.db.add_patient(patient)
        messagebox.showinfo("Success", f"Patient added successfully (ID: {new_id}).")

        # Reset form + refresh list
        self.clear_form()
        self._refresh_list()

    except ValueError as ve:
        # For expected issues like duplicates
        messagebox.showwarning("Cannot Add Patient", str(ve))

    except Exception as e:
        # For unexpected errors
        messagebox.showerror("Error", f"Failed to add patient: {e}")




    def update_patient(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a patient to update")
            return
        pid = self.tree.item(sel[0])["values"][0]
        birth_iso = self._get_birthdate_iso()
        if not birth_iso:
            messagebox.showwarning("Validation", "Birthdate is required. Please select month, day and year.")
            return
        patient = self._collect_patient_from_form()
        try:
            self.db.update_patient(pid, patient)
            messagebox.showinfo("Success", "Patient updated.")
            self.clear_form()
            self._refresh_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update patient: {e}")
            

    def delete_patient(self, patient_id: int) -> None:
        """Delete patient and clean up orphaned address/diagnosis rows if unused."""
        if not patient_id:
            return
        with self._conn() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cur = conn.cursor()
            # get the referenced ids first
            cur.execute("SELECT address_id, diagnosis_id FROM patients WHERE id = ?", (patient_id,))
            row = cur.fetchone()
            if not row:
                return
            address_id, diagnosis_id = row[0], row[1]

            # delete patient
            cur.execute("DELETE FROM patients WHERE id = ?", (patient_id,))

            # if no other patient references the address, delete it
            if address_id is not None:
                cur.execute("SELECT COUNT(*) FROM patients WHERE address_id = ?", (address_id,))
                cnt = cur.fetchone()[0]
                if cnt == 0:
                    cur.execute("DELETE FROM addresses WHERE id = ?", (address_id,))

            # if no other patient references the diagnosis, delete it
            if diagnosis_id is not None:
                cur.execute("SELECT COUNT(*) FROM patients WHERE diagnosis_id = ?", (diagnosis_id,))
                cnt = cur.fetchone()[0]
                if cnt == 0:
                    cur.execute("DELETE FROM diagnoses WHERE id = ?", (diagnosis_id,))

            conn.commit()



    # ---------------- List & Select ----------------
    def _refresh_list(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            rows = self.db.get_patients()
        except Exception:
            rows = []
        for r in rows:
            pid = r[0]
            first = r[1] or ""
            last = r[3] or ""
            bdate = r[6] or ""
            age = self._calculate_age(bdate) if bdate else ""
            sex = r[5] or ""
            contact = r[7] or ""
            muni = r[11] or ""
            brgy = r[12] or ""
            diag = r[10] or ""
            self.tree.insert("", "end", values=(pid, first, last, bdate, age, sex, contact, muni, brgy, diag))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        pid = self.tree.item(sel[0])["values"][0]
        # Prefer joined get_patients() view to populate form (more fields present)
        rows = self.db.get_patients()
        row = None
        for r in rows:
            if r[0] == pid:
                row = r
                break
        # If not found, fallback to get_patient (maybe different schema)
        if row is None:
            rec = self.db.get_patient(pid)
            if not rec:
                return
            # rec may be tuple or dict; handle both
            if isinstance(rec, dict):
                data = rec
                # simple mapping to form fields
                self._vars["First name"].set(data.get("first_name","") or "")
                self._vars["Middle name"].set(data.get("middle_name","") or "")
                self._vars["Last name"].set(data.get("last_name","") or "")
                self._vars["Suffix"].set(data.get("suffix","") or "")
                self._vars["Sex"].set(data.get("sex","Male"))
                bd = data.get("birthdate","")
                if bd:
                    try:
                        y,m,d = bd.split("-")
                        months_inv = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun",
                                      "07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec"}
                        self._vars["BD_year"].set(y)
                        self._vars["BD_month"].set(months_inv.get(m,""))
                        self._vars["BD_day"].set(str(int(d)))
                    except Exception:
                        self._vars["BD_year"].set(""); self._vars["BD_month"].set(""); self._vars["BD_day"].set("")
                self._vars["Contact No."].set(data.get("contact_no","") or "")
                self._vars["Height (cm)"].set("" if data.get("height_cm") is None else str(data.get("height_cm")))
                self._vars["Weight (kg)"].set("" if data.get("weight_kg") is None else str(data.get("weight_kg")))
                self._vars["Municipality/City"].set(data.get("municipality","") or "")
                self._on_muni_selected()
                self._vars["Barangay"].set(data.get("barangay","") or "")
                self._vars["House/Unit No."].set(data.get("house_no","") or "")
                self._vars["Street"].set(data.get("street","") or "")
                self._vars["Postal Code"].set(data.get("postal_code","") or "")
                diag = data.get("diagnosis","")
                if diag in COMMON_DIAGNOSES:
                    self._vars["Diagnosis_choice"].set("common"); self._on_diag_choice()
                    self._vars["Common diagnosis"].set(diag)
                else:
                    self._vars["Diagnosis_choice"].set("other"); self._on_diag_choice()
                    self._vars["Other diagnosis"].set(diag or "")
                self.notes_text.delete("1.0","end"); self.notes_text.insert("1.0", data.get("notes","") or "")
                return
            else:
                # tuple fallback: can't map reliably, so bail
                return

        # row found - layout according to get_patients join
        # (id, first_name, middle_name, last_name, suffix, sex, birthdate,
        #  contact_no, height_cm, weight_kg, diagnosis,
        #  municipality, barangay, street, house_no, postal_code,
        #  notes, created_at, updated_at)
        r = row
        self._vars["First name"].set(r[1] or "")
        self._vars["Middle name"].set(r[2] or "")
        self._vars["Last name"].set(r[3] or "")
        self._vars["Suffix"].set(r[4] or "")
        self._vars["Sex"].set(r[5] or "Male")
        bd = r[6] or ""
        if bd:
            try:
                y, m, d = bd.split("-")
                months_inv = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun",
                              "07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec"}
                self._vars["BD_year"].set(y); self._vars["BD_month"].set(months_inv.get(m,"")); self._vars["BD_day"].set(str(int(d)))
            except Exception:
                self._vars["BD_year"].set(""); self._vars["BD_month"].set(""); self._vars["BD_day"].set("")
        else:
            self._vars["BD_year"].set(""); self._vars["BD_month"].set(""); self._vars["BD_day"].set("")
        self._vars["Contact No."].set(r[7] or "")
        self._vars["Height (cm)"].set("" if r[8] is None else str(r[8]))
        self._vars["Weight (kg)"].set("" if r[9] is None else str(r[9]))
        self._vars["Municipality/City"].set(r[11] or "")
        self._on_muni_selected()
        self._vars["Barangay"].set(r[12] or "")
        self._vars["House/Unit No."].set(r[14] or "")
        self._vars["Street"].set(r[13] or "")
        self._vars["Postal Code"].set(r[15] or "")
        # notes
        self.notes_text.delete("1.0","end"); self.notes_text.insert("1.0", r[16] or "")
        diag_name = r[10] or ""
        if diag_name in COMMON_DIAGNOSES:
            self._vars["Diagnosis_choice"].set("common")
            self._vars["Common diagnosis"].set(diag_name)
            self._on_diag_choice()
        elif diag_name:
            self._vars["Diagnosis_choice"].set("other")
            self._vars["Other diagnosis"].set(diag_name)
            self._on_diag_choice()
        else:
            self._vars["Diagnosis_choice"].set("common"); self._vars["Common diagnosis"].set("")
            self._on_diag_choice()

    # ---------------- Exports & Reports ----------------
    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not path:
            return
        rows = self.db.get_patients()
        if not rows:
            messagebox.showinfo("Export", "No records to export.")
            return
        headers = ["id","first_name","middle_name","last_name","suffix","sex","birthdate",
                   "contact_no","height_cm","weight_kg","diagnosis","municipality","barangay",
                   "street","house_no","postal_code","notes","created_at","updated_at"]
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for r in rows:
                    writer.writerow(r)
            messagebox.showinfo("Export", f"Exported to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}")

    def generate_report(self):
        try:
            df = db_to_dataframe(self.db.db_name)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to build dataframe: {e}")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if not path:
            return
        try:
            generate_pdf_report(df, pdf_path=path)
            messagebox.showinfo("Report", f"PDF report saved to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {e}")

# ---------------- start ----------------
def start_app(fullscreen: bool = True, address_json: str | None = None):
    address_data = load_address_data(address_json) if address_json else load_address_data()
    root = tb.Window(themename=THEME)
    if fullscreen:
        root.attributes("-fullscreen", False)
    app = PMRSApp(root, address_data=address_data)
    root.mainloop()

if __name__ == "__main__":
    start_app()
