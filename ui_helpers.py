# ui_helpers.py
# UI helper functions for gui.py (birthdate helpers, compose/parse, clearing, age calculation)
import datetime
import calendar
from typing import Dict

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
        return max(age, 0)
    except Exception:
        return 0


def update_days(entries: Dict[str, object]) -> None:
    """
    Update the day combobox values based on the selected year/month in entries.
    entries must contain 'birth_year', 'birth_month', 'birth_day' combobox widgets.
    """
    y = entries.get('birth_year').get() if entries.get('birth_year') else ''
    m = entries.get('birth_month').get() if entries.get('birth_month') else ''
    day_widget = entries.get('birth_day')
    if not day_widget:
        return

    if not y or not m:
        days = [f"{d:02d}" for d in range(1, 32)]
        try:
            day_widget['values'] = days
        except Exception:
            # fallback for some widget implementations
            try:
                day_widget.config(values=days)
            except Exception:
                pass
        return

    try:
        year = int(y)
        month = int(m.split(' - ')[0])
    except Exception:
        return

    try:
        days_in_month = calendar.monthrange(year, month)[1]
    except Exception:
        days_in_month = 31

    days = [f"{d:02d}" for d in range(1, days_in_month + 1)]
    current_day = day_widget.get()
    try:
        day_widget['values'] = days
    except Exception:
        try:
            day_widget.config(values=days)
        except Exception:
            pass

    if current_day in days:
        try:
            day_widget.set(current_day)
        except Exception:
            pass
    else:
        try:
            day_widget.set('')
        except Exception:
            pass


def compose_birthdate(entries: Dict[str, object]) -> str:
    """
    Compose a YYYY-MM-DD string from entries['birth_year'], ['birth_month'], ['birth_day'].
    Returns '' if incomplete or invalid.
    """
    year_w = entries.get('birth_year')
    month_w = entries.get('birth_month')
    day_w = entries.get('birth_day')
    if not (year_w and month_w and day_w):
        return ''
    y = year_w.get().strip()
    m = month_w.get().strip()
    d = day_w.get().strip()
    if not (y and m and d):
        return ''
    try:
        month_num = int(m.split(' - ')[0])
        return f"{int(y):04d}-{int(month_num):02d}-{int(d):02d}"
    except Exception:
        return ''


def set_birthdate_widgets(entries: Dict[str, object], date_str: str) -> None:
    """
    Given entries dict and a date_str 'YYYY-MM-DD', set the birth_year/month/day widgets.
    If date_str is falsy or invalid, clears the widgets.
    """
    year_w = entries.get('birth_year')
    month_w = entries.get('birth_month')
    day_w = entries.get('birth_day')
    if not (year_w and month_w and day_w):
        return

    if not date_str:
        try:
            year_w.set(''); month_w.set(''); day_w.set('')
        except Exception:
            try:
                year_w.set(''); month_w.set(''); day_w.set('')
            except Exception:
                pass
        return

    try:
        parts = date_str.split('-')
        if len(parts) != 3:
            raise ValueError('Invalid date parts')
        y, m, d = parts
        m_int = int(m)
        month_display = f"{m_int:02d} - {calendar.month_name[m_int]}"
        year_w.set(y)
        month_w.set(month_display)
        # update days list to match month/year
        update_days(entries)
        day_w.set(f"{int(d):02d}")
    except Exception:
        try:
            year_w.set(''); month_w.set(''); day_w.set('')
        except Exception:
            pass


def clear_form_entries(entries: Dict[str, object]) -> None:
    """
    Clears all widgets in entries. Works with ttk.Entry/ttk.Combobox that support .delete/.set.
    """
    for k, widget in entries.items():
        try:
            # combobox-like (has set)
            if hasattr(widget, 'set'):
                widget.set('')
            else:
                widget.delete(0, 'end')
        except Exception:
            try:
                widget.delete(0, 'end')
            except Exception:
                try:
                    widget.set('')
                except Exception:
                    pass
