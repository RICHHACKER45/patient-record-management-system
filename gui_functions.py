# ----------------------------
# FILE: gui_functions.py
# GUI handlers that call PatientCRUD methods (moved out of gui.py)
# ----------------------------
from typing import Callable, Dict, Any, List
from tkinter import messagebox, filedialog
from crud import PatientCRUD
import calendar

# create a module-level CRUD instance (so callers don't have to instantiate)
crud = PatientCRUD()


# ----------------------------
# Helpers: compose / read form
# ----------------------------
def _compose_birthdate(entries: Dict[str, Any]) -> str:
    """Expect entries contains 'birth_year','birth_month','birth_day' as Combobox widgets."""
    y = entries.get('birth_year').get().strip() if entries.get('birth_year') else ''
    m = entries.get('birth_month').get().strip() if entries.get('birth_month') else ''
    d = entries.get('birth_day').get().strip() if entries.get('birth_day') else ''
    if not (y and m and d):
        return ''
    month_num = m.split(' - ')[0]
    try:
        return f"{int(y):04d}-{int(month_num):02d}-{int(d):02d}"
    except Exception:
        return ''


def read_form(entries: Dict[str, Any]) -> Dict[str, str]:
    """
    Read values directly from widgets in `entries` (widgets are ttk.Entry or ttk.Combobox).
    Returns a dict compatible with PatientCRUD.add/update_patient.
    """
    def _get(k):
        w = entries.get(k)
        if not w:
            return ''
        try:
            return w.get().strip()
        except Exception:
            try:
                # Entry-like may require get(0, END) but .get() is standard for ttk.Entry/Combobox
                return w.get().strip()
            except Exception:
                return ''

    return {
        'first_name': _get('first_name'),
        'middle_name': _get('middle_name'),
        'last_name': _get('last_name'),
        'name_ext': _get('name_ext'),
        'birthdate': _compose_birthdate(entries),
        'gender': _get('gender'),
        'contact': _get('contact'),
        'address': _get('address'),
        'diagnosis': _get('diagnosis'),
        'notes': _get('notes'),
    }


# ----------------------------
# CRUD handlers called by GUI
# Each handler receives:
# - entries: the dict of widgets used for the form
# - tree: the Treeview widget (for selection, optional)
# - refresh_cb: callable to refresh the GUI list (usually app._refresh_list)
# - clear_cb: callable to clear the form (usually app._clear_form)
# ----------------------------
def add_patient(entries: Dict[str, Any], tree, refresh_cb: Callable, clear_cb: Callable) -> None:
    try:
        data = read_form(entries)
    except Exception as e:
        messagebox.showerror('Error', f'Invalid input: {e}')
        return

    if not data['first_name'] or not data['last_name'] or not data['birthdate']:
        messagebox.showwarning('Missing', 'Please fill First name, Last name, and Birthdate.')
        return

    pid = crud.add_patient(data)
    if pid == -1:
        messagebox.showwarning('Duplicate', 'A patient with the same name and birthdate already exists.')
        return

    messagebox.showinfo('Added', f'Patient added with id {pid}')
    clear_cb()
    refresh_cb()


def update_patient(entries: Dict[str, Any], tree, refresh_cb: Callable, clear_cb: Callable) -> None:
    sel = tree.selection()
    if not sel:
        messagebox.showwarning('Select', 'Select a patient to update')
        return

    pid_text = tree.item(sel[0])['text']
    try:
        pid = int(pid_text)
    except Exception:
        messagebox.showerror('Error', 'Invalid selection (missing id).')
        return

    try:
        data = read_form(entries)
    except Exception as e:
        messagebox.showerror('Error', f'Invalid input: {e}')
        return

    if not data['first_name'] or not data['last_name'] or not data['birthdate']:
        messagebox.showwarning('Missing', 'Please fill First name, Last name, and Birthdate.')
        return

    res = crud.update_patient(pid, data)
    if res == -1:
        messagebox.showwarning('Duplicate', 'Another patient already exists with the same name and birthdate.')
        return
    elif res == 0:
        messagebox.showinfo('No change', 'No record was updated (maybe the record was removed).')
        refresh_cb()
        return
    else:
        messagebox.showinfo('Updated', 'Patient updated successfully.')
        clear_cb()
        refresh_cb()


def delete_patient(tree, refresh_cb: Callable) -> None:
    sel = tree.selection()
    if not sel:
        messagebox.showwarning('Select', 'Select a patient to delete')
        return

    pid_text = tree.item(sel[0])['text']
    try:
        pid = int(pid_text)
    except Exception:
        messagebox.showerror('Error', 'Invalid selection (missing id).')
        return

    if messagebox.askyesno('Confirm', 'Delete this patient?'):
        ok = crud.delete_patient(pid)
        if ok:
            messagebox.showinfo('Deleted', 'Patient deleted.')
        else:
            messagebox.showwarning('Failed', 'Could not delete patient (maybe already removed).')
        refresh_cb()


def export_csv(path: str) -> None:
    if not path:
        return
    try:
        crud.export_csv(path)
        messagebox.showinfo('Export', f'Exported to {path}')
    except Exception as e:
        messagebox.showerror('Export failed', f'Could not export CSV: {e}')


def get_patient(pid: int) -> dict:
    try:
        return crud.get_patient(pid)
    except Exception:
        return {}


def list_patients() -> List[dict]:
    return crud.list_patients()


def search_patients(term: str) -> List[dict]:
    term = (term or '').strip().lower()
    if not term:
        return list_patients()
    allp = list_patients()
    filtered = [
        p for p in allp
        if term in (p.get('first_name','') or '').lower()
        or term in (p.get('last_name','') or '').lower()
        or term in (p.get('middle_name','') or '').lower()
    ]
    return filtered


# Optional helper: fill birthdate dropdown day list based on year/month (utility that GUI can call)
def compute_days_for_month(year: int, month: int) -> list:
    try:
        days = calendar.monthrange(year, month)[1]
        return [f"{d:02d}" for d in range(1, days + 1)]
    except Exception:
        return [f"{d:02d}" for d in range(1, 32)]
