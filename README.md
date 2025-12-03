<h1 align="center" style="
  font-size: 62px;
  font-weight: 900;
  background: linear-gradient(to right, #0062ff, #00c2ff);
  -webkit-background-clip: text;
  color: transparent;">
  Patient Medical Record System (PMRS)
</h1>

<p align="center">
  <strong>A modern, GUI-based patient management system built with Python, Tkinter, and SQLite.</strong><br>
  Designed for simplicity, readability, and modularity — created as a case study project.
</p>

---

## 🚀 Overview

PMRS is a **desktop application** that allows users to manage patient records efficiently.  
It includes features such as:

- Adding, updating, deleting, and searching patient records  
- Birthdate dropdown with auto-adjusting days (handles leap years)  
- CSV export  
- Automatic age computation  
- PDF report generation  
- Clean code structure using helpers, CRUD modules, and UI utilities  

The project started as a school requirement, but it eventually grew into a fully functioning system as I kept refining and learning Python along the way.

Yes — some parts are *vibe-coded* early on, but through refactoring and modularity, the project became clean and highly maintainable.

---

## ✨ Features

### 🧑‍⚕️ Patient Management  
- Add, update, delete patient records  
- Automatic age calculation  
- Birthdate selection using **year/month/day dropdowns**  
- Form auto-fill when selecting a record  

### 🔍 Search & Filtering  
- Search patients by name  
- Real-time refresh  

### 📊 Reporting  
- Export database to CSV  
- Generate PDF summary reports with charts  

### 🛠️ Modular Architecture  
The codebase is cleanly divided into:

/crud/ → Handles database operations
/gui_functions/ → Logic linked to GUI actions
/ui_helpers/ → UI components and reusable helper methods
/gui.py → Main application interface



This makes the project scalable, easier to maintain, and beginner-friendly for others reading the code.

---

## 📚 What I Learned

This case study taught me:

- How to design GUIs using **Tkinter** and **ttk widgets**  
- How to refactor large scripts into modular Python files  
- How CRUD operations integrate with real applications  
- How to generate PDFs, reports, and structured UI components  
- How to handle dropdown dependencies (dynamic day counts, month parsing, etc.)  
- How to balance “school-project goals” with “real-world code quality”  

Most importantly:  
I learned how to take messy, rushed code and turn it into something clean, readable, and expandable.

---

## 🖼️ Screenshots (Optional)

> Add your screenshots here if you want:  
> `./assets/screenshot_main.png`  
> `./assets/screenshot_form.png`

---

## 🧩 Tech Stack

- **Python 3.x**  
- **Tkinter & ttk** (GUI)  
- **SQLite** (database)  
- **Pandas** (data handling)  
- **Matplotlib / ReportLab** (PDF report generation)

---

## 🏁 How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python gui.py


📌 Notes

This system is created as a school case study, but the code is structured enough to evolve into a real application.

Built with love, debugging, coffee, and the occasional “vibe coding” moment.

📝 License

This project is open for educational and personal use.