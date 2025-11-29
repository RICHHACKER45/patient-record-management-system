# ----------------------------
# FILE: gui.py
# Modern PMRS GUI using ttkbootstrap
# ----------------------------
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
from crud import PatientCRUD
from data_utils import db_to_dataframe
from graph_report import generate_pdf_report

class PMRSApp:
    def __init__(self, root, crud_obj):
        self.root = root
        self.root.title('PMRS - Patient Management Record System')
        self.root.geometry('950x600')
        self.crud = crud_obj

        # ttkbootstrap style
        self.style = tb.Style()

        # Build the UI
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        # Main frame
        main_frame = tb.Frame(self.root, padding=10)
        main_frame.pack(fill='both', expand=True)

        # ----- Left Frame: Form -----
        form_frame = tb.Labelframe(main_frame, text='Patient Form', padding=10)
        form_frame.pack(side=LEFT, fill='y', padx=(0,10))

        labels = ['First name','Last name','Age','Gender','Contact','Diagnosis','Notes']
        self.entries = {}
        for i, l in enumerate(labels):
            tb.Label(form_frame, text=l).grid(row=i, column=0, sticky='w', pady=4)
            ent = tb.Entry(form_frame, width=30)
            ent.grid(row=i, column=1, pady=4, sticky='w')
            self.entries[l.lower().replace(' ','_')] = ent

        # Buttons (modern style)
        btn_frame = tb.Frame(form_frame)
        btn_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)

        tb.Button(btn_frame, text='Add', bootstyle='success-outline', width=12, command=self.add_patient).grid(row=0, column=0, padx=5, pady=2)
        tb.Button(btn_frame, text='Update', bootstyle='primary-outline', width=12, command=self.update_patient).grid(row=0, column=1, padx=5, pady=2)
        tb.Button(btn_frame, text='Delete', bootstyle='danger-outline', width=12, command=self.delete_patient).grid(row=1, column=0, padx=5, pady=2)
        tb.Button(btn_frame, text='Export JSON', bootstyle='info-outline', width=12, command=self.export_json).grid(row=1, column=1, padx=5, pady=2)
        tb.Button(btn_frame, text='Generate Report', bootstyle='warning-outline', width=25, command=self.generate_report).grid(row=2, column=0, columnspan=2, pady=5)

        # ----- Right Frame: Patient List -----
        list_frame = tb.Labelframe(main_frame, text='Patient Records', padding=10)
        list_frame.pack(side=RIGHT, fill='both', expand=True)

        cols = ('id','first_name','last_name','age','gender','contact')
        self.tree = tb.Treeview(list_frame, columns=cols, show='headings', bootstyle="info")
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=100)
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # Optional: search bar
        search_frame = tb.Frame(list_frame)
        search_frame.pack(fill='x', pady=5)
        tb.Label(search_frame, text="Search by Name:").pack(side=LEFT)
        self.search_var = tb.StringVar()
        tb.Entry(search_frame, textvariable=self.search_var, width=30).pack(side=LEFT, padx=5)
        tb.Button(search_frame, text='Search', bootstyle='primary-outline', command=self.search_patient).pack(side=LEFT)

    # --------------------
    # CRUD methods
    # --------------------
    def _refresh_list(self, patients=None):
        for r in self.tree.get_children():
            self.tree.delete(r)
        if patients is None:
            patients = self.crud.list_patients()
        for p in patients:
            self.tree.insert('', 'end', values=(p['id'], p['first_name'], p['last_name'], p['age'], p['gender'], p['contact']))

    def _read_form(self):
        return {
            'first_name': self.entries['first_name'].get(),
            'last_name': self.entries['last_name'].get(),
            'age': int(self.entries['age'].get() or 0),
            'gender': self.entries['gender'].get(),
            'contact': self.entries['contact'].get(),
            'diagnosis': self.entries['diagnosis'].get(),
            'notes': self.entries['notes'].get()
        }

    def add_patient(self):
        try:
            data = self._read_form()
        except Exception as e:
            messagebox.showerror('Error', f'Invalid input: {e}')
            return
        pid = self.crud.add_patient(data)
        messagebox.showinfo('Added', f'Patient added with id {pid}')
        self._refresh_list()

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        pid = vals[0]
        p = self.crud.get_patient(pid)
        if not p:
            return
        for k in self.entries:
            self.entries[k].delete(0,'end')
            self.entries[k].insert(0, p.get(k,''))

    def update_patient(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Select', 'Select a patient to update')
            return
        pid = self.tree.item(sel[0])['values'][0]
        data = self._read_form()
        ok = self.crud.update_patient(pid, data)
        messagebox.showinfo('Updated', f'Updated: {ok}')
        self._refresh_list()

    def delete_patient(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Select', 'Select a patient to delete')
            return
        pid = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno('Confirm', 'Delete this patient?'):
            self.crud.delete_patient(pid)
            self._refresh_list()

    def export_json(self):
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
        if not path:
            return
        self.crud.export_json(path)
        messagebox.showinfo('Export', f'Exported to {path}')

    def generate_report(self):
        df = db_to_dataframe(self.crud.db_path)
        path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF','*.pdf')])
        if not path:
            return
        generate_pdf_report(df, pdf_path=path)
        messagebox.showinfo('Report', f'Report saved to {path}')

    # --------------------
    # Search
    # --------------------
    def search_patient(self):
        term = self.search_var.get().lower()
        filtered = [p for p in self.crud.list_patients() if term in p['first_name'].lower() or term in p['last_name'].lower()]
        self._refresh_list(filtered)


# ----------------------------
# Start the app
# ----------------------------
def start_app():
    root = tb.Window(themename="superhero")
    crud = PatientCRUD()
    app = PMRSApp(root, crud)
    root.mainloop()
    