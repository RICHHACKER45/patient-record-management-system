# ----------------------------
# FILE: gui.py
# Tkinter-based GUI. Encapsulated inside class PMRSApp and function start_app().
# ----------------------------
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class PMRSApp:
    def __init__(self, root, crud_obj):
        self.root = root
        self.root.title('PMRS - Patient Management Record System')
        self.crud = crud_obj
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        frm = ttk.Frame(self.root, padding=8)
        frm.pack(fill='both', expand=True)

        # Form
        form = ttk.LabelFrame(frm, text='Patient Form', padding=8)
        form.pack(side='top', fill='x')
        labels = ['First name','Last name','Age','Gender','Contact','Diagnosis','Notes']
        self.entries = {}
        for i,l in enumerate(labels):
            ttk.Label(form, text=l).grid(row=i, column=0, sticky='w')
            ent = ttk.Entry(form, width=40)
            ent.grid(row=i, column=1, sticky='w')
            self.entries[l.lower().replace(' ','_')] = ent

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=0, column=2, rowspan=3, padx=8)
        ttk.Button(btn_frame, text='Add', command=self.add_patient).pack(fill='x')
        ttk.Button(btn_frame, text='Update', command=self.update_patient).pack(fill='x')
        ttk.Button(btn_frame, text='Delete', command=self.delete_patient).pack(fill='x')
        ttk.Button(btn_frame, text='Export JSON', command=self.export_json).pack(fill='x')
        ttk.Button(btn_frame, text='Generate Report', command=self.generate_report).pack(fill='x')

        # List
        list_frame = ttk.LabelFrame(frm, text='Patients', padding=4)
        list_frame.pack(fill='both', expand=True)
        cols = ('id','first_name','last_name','age','gender','contact')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings', selectmode='browse')
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=100)
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

    def _refresh_list(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        for p in self.crud.list_patients():
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
        # populate form
        self.entries['first_name'].delete(0,'end'); self.entries['first_name'].insert(0,p.get('first_name',''))
        self.entries['last_name'].delete(0,'end'); self.entries['last_name'].insert(0,p.get('last_name',''))
        self.entries['age'].delete(0,'end'); self.entries['age'].insert(0,str(p.get('age','')))
        self.entries['gender'].delete(0,'end'); self.entries['gender'].insert(0,p.get('gender',''))
        self.entries['contact'].delete(0,'end'); self.entries['contact'].insert(0,p.get('contact',''))
        self.entries['diagnosis'].delete(0,'end'); self.entries['diagnosis'].insert(0,p.get('diagnosis',''))
        self.entries['notes'].delete(0,'end'); self.entries['notes'].insert(0,p.get('notes',''))

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
        p = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
        if not p:
            return
        self.crud.export_json(p)
        messagebox.showinfo('Export', f'Exported to {p}')

    def generate_report(self):
        # gather df and call graph_report to make pdf
        from data_utils import db_to_dataframe
        from graph_report import generate_pdf_report
        df = db_to_dataframe(self.crud.db_path)
        path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF','*.pdf')])
        if not path:
            return
        generate_pdf_report(df, pdf_path=path)
        messagebox.showinfo('Report', f'Report saved to {path}')

def start_app():
    root = tk.Tk()
    from crud import PatientCRUD
    crud = PatientCRUD()
    app = PMRSApp(root, crud)
    root.mainloop()
