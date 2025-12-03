# ----------------------------
# FILE: gui.py
# PMRS GUI using standard tkinter + ttk (no ttkbootstrap)
# ----------------------------
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from crud import PatientCRUD
from data_utils import db_to_dataframe
from graph_report import generate_pdf_report
import datetime
import calendar


def compute_age_from_birthdate(birthdate: str) -> int:
    """
    birthdate expected as YYYY-MM-DD; returns age in years (int).
    If invalid or empty returns 0.
    """
    if not birthdate:
        return 0
    try:
        y, m, d = birthdate.split('-')
        bd = datetime.date(int(y), int(m), int(d))
        today = datetime.date.today()
        age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
        return age if age >= 0 else 0
    except Exception:
        return 0


class PMRSApp:
    def __init__(self, root, crud_obj):
        self.root = root
        self.root.title('PMRS - Patient Management Record System')
        self.root.geometry('1150x700')
        self.crud = crud_obj

        # Build the UI
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left: Form
        form_frame = ttk.LabelFrame(main_frame, text='Patient Form', padding=10)
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12), pady=6)

        # make column 1 expandable for long fields
        form_frame.columnconfigure(1, weight=1)

        labels = [
            'First name', 'Middle name', 'Last name', 'Name Ext',
            'Birthdate (Year/Month/Day)', 'Gender', 'Contact',
            'Address', 'Diagnosis', 'Notes'
        ]

        self.entries = {}
        ENTRY_WIDTH = 32
        COMBO_WIDTH = 18
        NAME_EXT_OPTIONS = ['Jr.', 'Sr.', 'II', 'III', 'IV']

        # Create form rows
        for i, label in enumerate(labels):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky='w', pady=6, padx=(0, 6))
            key = label.split('(')[0].strip().lower().replace(' ', '_')

            if key == 'name_ext':
                cb = ttk.Combobox(form_frame, width=COMBO_WIDTH, values=NAME_EXT_OPTIONS)
                cb.grid(row=i, column=1, sticky='w', pady=6)
                self.entries['name_ext'] = cb
                continue

            if key == 'gender':
                cb = ttk.Combobox(form_frame, width=COMBO_WIDTH, values=['Male', 'Female', 'Other'])
                cb.grid(row=i, column=1, sticky='w', pady=6)
                self.entries['gender'] = cb
                continue

            if key == 'birthdate':
                # placeholder row - actual widgets are created below inside birth_frame
                self.birth_row_index = i
                placeholder = ttk.Frame(form_frame, height=1)
                placeholder.grid(row=i, column=1, sticky='w', pady=6)
                continue

            ent = ttk.Entry(form_frame, width=ENTRY_WIDTH)
            ent.grid(row=i, column=1, sticky='w', pady=6)
            self.entries[key] = ent

        # Birthdate dropdowns inside a small frame (year / month / day)
        cur_year = datetime.datetime.now().year
        years = [str(y) for y in range(cur_year, cur_year - 120, -1)]
        months = [f"{m:02d} - {calendar.month_name[m]}" for m in range(1, 13)]
        days = [f"{d:02d}" for d in range(1, 32)]

        birth_frame = ttk.Frame(form_frame)
        birth_frame.grid(row=self.birth_row_index, column=1, sticky='w', pady=6)

        year_cb = ttk.Combobox(birth_frame, width=8, values=years)
        month_cb = ttk.Combobox(birth_frame, width=16, values=months)
        day_cb = ttk.Combobox(birth_frame, width=6, values=days)

        year_cb.grid(row=0, column=0, sticky='w')
        month_cb.grid(row=0, column=1, padx=(8, 0), sticky='w')
        day_cb.grid(row=0, column=2, padx=(8, 0), sticky='w')

        self.entries['birth_year'] = year_cb
        self.entries['birth_month'] = month_cb
        self.entries['birth_day'] = day_cb

        # Bind change events to update days
        year_cb.bind('<<ComboboxSelected>>', lambda e: self._update_days())
        month_cb.bind('<<ComboboxSelected>>', lambda e: self._update_days())

        # Buttons (2x3 grid)
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=len(labels) + 1, column=0, columnspan=2, pady=(12, 0), sticky='w')

        BTN_W = 16
        add_btn = ttk.Button(btn_frame, text='Add', width=BTN_W, command=self.add_patient)
        update_btn = ttk.Button(btn_frame, text='Update', width=BTN_W, command=self.update_patient)
        clear_btn = ttk.Button(btn_frame, text='Clear', width=BTN_W, command=self._clear_form)
        delete_btn = ttk.Button(btn_frame, text='Delete', width=BTN_W, command=self.delete_patient)
        export_btn = ttk.Button(btn_frame, text='Export CSV', width=BTN_W, command=self.export_csv)
        report_btn = ttk.Button(btn_frame, text='Generate Report', width=BTN_W, command=self.generate_report)

        add_btn.grid(row=0, column=0, padx=6, pady=6)
        update_btn.grid(row=0, column=1, padx=6, pady=6)
        clear_btn.grid(row=0, column=2, padx=6, pady=6)
        delete_btn.grid(row=1, column=0, padx=6, pady=6)
        export_btn.grid(row=1, column=1, padx=6, pady=6)
        report_btn.grid(row=1, column=2, padx=6, pady=6)

        # Right: Patient list
        list_frame = ttk.LabelFrame(main_frame, text='Patient Records', padding=10)
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Visible columns (ID removed)
        cols = ('first_name', 'middle_name', 'last_name', 'name_ext', 'age', 'birthdate', 'gender', 'contact', 'address')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings')
        # hide the treeview's "#0" column (we'll store id in text)
        self.tree.column("#0", width=0, stretch=False)
        self.tree.heading("#0", text="")

        for c in cols:
            self.tree.heading(c, text=c.replace('_', ' ').title())
            width = 100
            if c == 'age':
                width = 60
            elif c in ('first_name', 'last_name', 'middle_name'):
                width = 120
            elif c == 'address':
                width = 260
            self.tree.column(c, width=width, anchor='center')

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # Search bar
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=8)
        ttk.Label(search_frame, text="Search by Name:").pack(side=tk.LEFT, padx=(0, 6))
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=36).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(search_frame, text='Search', command=self.search_patient).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(search_frame, text='Refresh', command=self._refresh_list).pack(side=tk.LEFT)

    # --------------------
    # Birth helpers
    # --------------------
    def _update_days(self):
        """Update day combobox values based on chosen year/month (handles leap years)."""
        y = self.entries['birth_year'].get()
        m = self.entries['birth_month'].get()
        if not y or not m:
            days = [f"{d:02d}" for d in range(1, 32)]
            try:
                self.entries['birth_day']['values'] = days
            except Exception:
                pass
            return
        try:
            year = int(y)
            month = int(m.split(' - ')[0])
        except Exception:
            return

        days_in_month = calendar.monthrange(year, month)[1]
        days = [f"{d:02d}" for d in range(1, days_in_month + 1)]
        current_day = self.entries['birth_day'].get()
        self.entries['birth_day']['values'] = days
        if current_day in days:
            self.entries['birth_day'].set(current_day)
        else:
            self.entries['birth_day'].set('')

    def _compose_birthdate(self) -> str:
        y = self.entries['birth_year'].get().strip()
        m = self.entries['birth_month'].get().strip()
        d = self.entries['birth_day'].get().strip()
        if not (y and m and d):
            return ''
        month_num = m.split(' - ')[0]
        try:
            return f"{int(y):04d}-{int(month_num):02d}-{int(d):02d}"
        except Exception:
            return ''

    def _set_birthdate_widgets(self, date_str: str):
        if not date_str:
            try:
                self.entries['birth_year'].set('')
                self.entries['birth_month'].set('')
                self.entries['birth_day'].set('')
            except Exception:
                pass
            return
        try:
            parts = date_str.split('-')
            if len(parts) != 3:
                raise ValueError
            y, m, d = parts
            m_int = int(m)
            month_display = f"{m_int:02d} - {calendar.month_name[m_int]}"
            self.entries['birth_year'].set(y)
            self.entries['birth_month'].set(month_display)
            self._update_days()
            self.entries['birth_day'].set(f"{int(d):02d}")
        except Exception:
            try:
                self.entries['birth_year'].set('')
                self.entries['birth_month'].set('')
                self.entries['birth_day'].set('')
            except Exception:
                pass

    # --------------------
    # CRUD methods
    # --------------------
    def _refresh_list(self, patients=None):
        for r in self.tree.get_children():
            self.tree.delete(r)
        if patients is None:
            patients = self.crud.list_patients()
        for p in patients:
            age = compute_age_from_birthdate(p.get('birthdate', ''))
            # store id in text (hidden), values exclude id
            self.tree.insert('', 'end', text=str(p.get('id', '')), values=(
                p.get('first_name', ''),
                p.get('middle_name', ''),
                p.get('last_name', ''),
                p.get('name_ext', ''),
                age,
                p.get('birthdate', ''),
                p.get('gender', ''),
                p.get('contact', ''),
                p.get('address', '')
            ))

    def _read_form(self):
        return {
            'first_name': self.entries.get('first_name').get().strip() if self.entries.get('first_name') else '',
            'middle_name': self.entries.get('middle_name').get().strip() if self.entries.get('middle_name') else '',
            'last_name': self.entries.get('last_name').get().strip() if self.entries.get('last_name') else '',
            'name_ext': self.entries.get('name_ext').get().strip() if self.entries.get('name_ext') else '',
            'birthdate': self._compose_birthdate(),
            'gender': self.entries.get('gender').get().strip() if self.entries.get('gender') else '',
            'contact': self.entries.get('contact').get().strip() if self.entries.get('contact') else '',
            'address': self.entries.get('address').get().strip() if self.entries.get('address') else '',
            'diagnosis': self.entries.get('diagnosis').get().strip() if self.entries.get('diagnosis') else '',
            'notes': self.entries.get('notes').get().strip() if self.entries.get('notes') else ''
        }

    def add_patient(self):
        try:
            data = self._read_form()
        except Exception as e:
            messagebox.showerror('Error', f'Invalid input: {e}')
            return

        if not data['first_name'] or not data['last_name'] or not data['birthdate']:
            messagebox.showwarning('Missing', 'Please fill First name, Last name, and Birthdate.')
            return

        pid = self.crud.add_patient(data)

        if pid == -1:
            messagebox.showwarning('Duplicate', 'A patient with the same name and birthdate already exists.')
            return

        messagebox.showinfo('Added', f'Patient added with id {pid}')
        self._clear_form()
        self._refresh_list()

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        pid_text = self.tree.item(sel[0])['text']
        try:
            pid = int(pid_text)
        except Exception:
            return
        p = self.crud.get_patient(pid)
        if not p:
            return

        for k, widget in self.entries.items():
            if k in ('birth_year', 'birth_month', 'birth_day'):
                continue
            val = p.get(k, '')
            try:
                if hasattr(widget, 'set'):
                    widget.set(val)
                else:
                    widget.delete(0, tk.END)
                    widget.insert(0, val)
            except Exception:
                try:
                    widget.delete(0, tk.END)
                    widget.insert(0, val)
                except Exception:
                    pass

        self._set_birthdate_widgets(p.get('birthdate', ''))

    def update_patient(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Select', 'Select a patient to update')
            return
        pid_text = self.tree.item(sel[0])['text']
        try:
            pid = int(pid_text)
        except Exception:
            messagebox.showerror('Error', 'Invalid selection (missing id).')
            return

        data = self._read_form()

        if not data['first_name'] or not data['last_name'] or not data['birthdate']:
            messagebox.showwarning('Missing', 'Please fill First name, Last name, and Birthdate.')
            return

        res = self.crud.update_patient(pid, data)
        if res == -1:
            messagebox.showwarning('Duplicate', 'Another patient already exists with the same name and birthdate.')
            return
        elif res == 0:
            messagebox.showinfo('No change', 'No record was updated (maybe the record was removed).')
            self._refresh_list()
            return
        else:
            messagebox.showinfo('Updated', 'Patient updated successfully.')
            self._clear_form()
            self._refresh_list()

    def delete_patient(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Select', 'Select a patient to delete')
            return
        pid_text = self.tree.item(sel[0])['text']
        try:
            pid = int(pid_text)
        except Exception:
            messagebox.showerror('Error', 'Invalid selection (missing id).')
            return

        if messagebox.askyesno('Confirm', 'Delete this patient?'):
            ok = self.crud.delete_patient(pid)
            if ok:
                messagebox.showinfo('Deleted', 'Patient deleted.')
            else:
                messagebox.showwarning('Failed', 'Could not delete patient (maybe already removed).')
            self._refresh_list()

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if not path:
            return
        try:
            self.crud.export_csv(path)
            messagebox.showinfo('Export', f'Exported to {path}')
        except Exception as e:
            messagebox.showerror('Export failed', f'Could not export CSV: {e}')

    def generate_report(self):
        df = db_to_dataframe(self.crud.db_path)
        path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF', '*.pdf')])
        if not path:
            return
        try:
            generate_pdf_report(df, pdf_path=path)
            messagebox.showinfo('Report', f'Report saved to {path}')
        except Exception as e:
            messagebox.showerror('Report failed', f'Could not generate report: {e}')

    # --------------------
    # Search
    # --------------------
    def search_patient(self):
        term = self.search_var.get().lower()
        filtered = [
            p for p in self.crud.list_patients()
            if term in (p.get('first_name', '').lower()) or term in (p.get('last_name', '').lower()) or term in (p.get('middle_name', '').lower())
        ]
        self._refresh_list(filtered)

    def _clear_form(self):
        # clear everything and set focus to first_name
        for k, widget in self.entries.items():
            try:
                if hasattr(widget, 'set'):
                    widget.set('')
                else:
                    widget.delete(0, tk.END)
            except Exception:
                try:
                    widget.delete(0, tk.END)
                except Exception:
                    pass
        # set focus to first name if available
        if 'first_name' in self.entries:
            try:
                self.entries['first_name'].focus_set()
            except Exception:
                pass


# ----------------------------
# Start the app
# ----------------------------
def start_app():
    root = tk.Tk()
    crud = PatientCRUD()
    app = PMRSApp(root, crud)
    root.mainloop()


if __name__ == '__main__':
    start_app()
