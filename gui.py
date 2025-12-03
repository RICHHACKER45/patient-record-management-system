# ----------------------------
# FILE: gui.py
# Refactored PMRS GUI (tkinter + ttk)
# UI helpers moved to ui_helpers.py, handlers remain in gui_functions.py
# ----------------------------
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import calendar

from data_utils import db_to_dataframe
from graph_report import generate_pdf_report

import gui_functions as gf
from crud import PatientCRUD  # optional ensure DB exists
from ui_helpers import (
    compute_age_from_birthdate,
    update_days,
    compose_birthdate,
    set_birthdate_widgets,
    clear_form_entries
)

DB = 'patients.db'


class PMRSApp:
    def __init__(self, root, crud_obj=None, db_path=DB):
        self.root = root
        self.root.title('PMRS - Patient Management Record System')
        self.root.geometry('1150x700')
        self.db_path = db_path

        # optional ensure DB/table exists
        self.crud = crud_obj or PatientCRUD(self.db_path)

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill='both', expand=True)

        # -- Left: Form --
        form = ttk.LabelFrame(main, text='Patient Form', padding=12)
        form.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        form.columnconfigure(1, weight=1)

        # schema: (label, key, widget, options)
        schema = [
            ('First name', 'first_name', 'entry', None),
            ('Middle name', 'middle_name', 'entry', None),
            ('Last name', 'last_name', 'entry', None),
            ('Name Ext', 'name_ext', 'combo', ['Jr.', 'Sr.', 'II', 'III', 'IV']),
            ('Birthdate (Year/Month/Day)', 'birthdate', 'birth', None),
            ('Gender', 'gender', 'combo', ['Male', 'Female', 'Other']),
            ('Contact', 'contact', 'entry', None),
            ('Address', 'address', 'entry', None),
            ('Diagnosis', 'diagnosis', 'entry', None),
            ('Notes', 'notes', 'entry', None),
        ]

        self.entries = {}
        ENTRY_W, COMBO_W = 32, 18

        for i, (lbl, key, wtype, opts) in enumerate(schema):
            ttk.Label(form, text=lbl).grid(row=i, column=0, sticky='w', pady=6, padx=(0, 6))
            if wtype == 'entry':
                e = ttk.Entry(form, width=ENTRY_W); e.grid(row=i, column=1, sticky='w', pady=6); self.entries[key] = e
            elif wtype == 'combo':
                cb = ttk.Combobox(form, width=COMBO_W, values=opts); cb.grid(row=i, column=1, sticky='w', pady=6); self.entries[key] = cb
            elif wtype == 'birth':
                # placeholder row - widgets added below
                self.birth_row = i
                ttk.Frame(form, height=1).grid(row=i, column=1, sticky='w', pady=6)

        # birth dropdowns
        cur = __import__('datetime').datetime.now().year
        years = [str(y) for y in range(cur, cur - 120, -1)]
        months = [f"{m:02d} - {calendar.month_name[m]}" for m in range(1, 13)]
        days = [f"{d:02d}" for d in range(1, 32)]

        bf = ttk.Frame(form); bf.grid(row=self.birth_row, column=1, sticky='w', pady=6)
        ycb = ttk.Combobox(bf, width=8, values=years); mcb = ttk.Combobox(bf, width=16, values=months); dcb = ttk.Combobox(bf, width=6, values=days)
        ycb.grid(row=0, column=0); mcb.grid(row=0, column=1, padx=(8,0)); dcb.grid(row=0, column=2, padx=(8,0))
        self.entries['birth_year'], self.entries['birth_month'], self.entries['birth_day'] = ycb, mcb, dcb
        # use ui_helpers.update_days
        ycb.bind('<<ComboboxSelected>>', lambda e: update_days(self.entries))
        mcb.bind('<<ComboboxSelected>>', lambda e: update_days(self.entries))

        # Buttons (2x3)
        btn_frame = ttk.Frame(form); btn_frame.grid(row=len(schema)+1, column=0, columnspan=2, pady=(12,0), sticky='w')
        BTN_W = 18
        buttons = [
            ('Add', lambda: gf.add_patient(self.entries, self.tree, self._refresh_list, self._clear_form)),
            ('Update', lambda: gf.update_patient(self.entries, self.tree, self._refresh_list, self._clear_form)),
            ('Clear', self._clear_form),
            ('Delete', lambda: gf.delete_patient(self.tree, self._refresh_list)),
            ('Export CSV', self._on_export_csv),
            ('Generate Report', self.generate_report)
        ]
        for idx, (txt, cmd) in enumerate(buttons):
            b = ttk.Button(btn_frame, text=txt, width=BTN_W, command=cmd)
            b.grid(row=idx//3, column=idx%3, padx=6, pady=6)

        for c in range(3):
            btn_frame.columnconfigure(c, weight=1)

        # -- Right: Treeview --
        listf = ttk.LabelFrame(main, text='Patient Records', padding=12)
        listf.pack(side=tk.RIGHT, fill='both', expand=True)

        cols = ('first_name', 'middle_name', 'last_name', 'name_ext', 'age', 'birthdate', 'gender', 'contact', 'address')
        self.tree = ttk.Treeview(listf, columns=cols, show='headings')
        # hide #0 but use text to store id
        self.tree.column("#0", width=0, stretch=False); self.tree.heading("#0", text="")

        for c in cols:
            self.tree.heading(c, text=c.replace('_', ' ').title())
            width = 100
            if c == 'age': width = 60
            elif c in ('first_name','middle_name','last_name'): width = 120
            elif c == 'address': width = 260
            self.tree.column(c, width=width, anchor='center')

        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # search bar
        sframe = ttk.Frame(listf); sframe.pack(fill='x', pady=8)
        ttk.Label(sframe, text="Search by Name:").pack(side=tk.LEFT, padx=(0,6))
        self.search_var = tk.StringVar()
        ttk.Entry(sframe, textvariable=self.search_var, width=36).pack(side=tk.LEFT, padx=(0,6))
        ttk.Button(sframe, text='Search', command=self.search_patient).pack(side=tk.LEFT, padx=(0,6))
        ttk.Button(sframe, text='Refresh', command=self._refresh_list).pack(side=tk.LEFT)

    # ---------- Data / UI helpers (these call ui_helpers) ----------
    def _refresh_list(self, patients=None):
        for r in self.tree.get_children():
            self.tree.delete(r)
        if patients is None:
            patients = gf.list_patients()
        for p in patients:
            age = compute_age_from_birthdate(p.get('birthdate',''))
            self.tree.insert('', 'end', text=str(p.get('id','')), values=(
                p.get('first_name',''), p.get('middle_name',''), p.get('last_name',''),
                p.get('name_ext',''), age, p.get('birthdate',''), p.get('gender',''),
                p.get('contact',''), p.get('address','')
            ))

    def _clear_form(self):
        # delegate to ui_helpers.clear_form_entries
        clear_form_entries(self.entries)
        # ensure focus returns to first_name
        if 'first_name' in self.entries:
            try:
                self.entries['first_name'].focus_set()
            except Exception:
                pass

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        pid_text = self.tree.item(sel[0])['text']
        try:
            pid = int(pid_text)
        except Exception:
            return
        p = gf.get_patient(pid)
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

        # delegate birthdate widget setting
        set_birthdate_widgets(self.entries, p.get('birthdate', ''))

    def _on_export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if not path:
            return
        gf.export_csv(path)

    def generate_report(self):
        df = db_to_dataframe(self.db_path)
        path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF', '*.pdf')])
        if not path:
            return
        try:
            generate_pdf_report(df, pdf_path=path)
            messagebox.showinfo('Report', f'Report saved to {path}')
        except Exception as e:
            messagebox.showerror('Report failed', f'Could not generate report: {e}')

    def search_patient(self):
        term = self.search_var.get().lower()
        filtered = gf.search_patients(term)
        self._refresh_list(filtered)


# ----------------------------
# Start the app (left here as you requested)
# ----------------------------
def start_app():
    root = tk.Tk()
    app = PMRSApp(root)
    root.mainloop()


if __name__ == '__main__':
    start_app()
