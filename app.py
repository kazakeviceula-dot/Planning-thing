import tkinter as tk
from tkinter import ttk, messagebox
from models import StudyManager, Test

class IBPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ula's IB Workload Manager")
        self.root.geometry("900x600")
        self.manager = StudyManager()

        # Create Tab Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Tabs setup
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.tab_tests = ttk.Frame(self.notebook)
        self.tab_availability = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_dashboard, text="Tab 1: Dashboard")
        self.notebook.add(self.tab_tests, text="Tab 2: Tests and Topics")
        self.notebook.add(self.tab_availability, text="Tab 3: Availability")

        self.build_test_tab()

    def build_test_tab(self):
        ttk.Label(self.tab_tests, text="Add New Exam", font=("Arial", 14, "bold")).pack(pady=10)
        # Add Input fields for Subject, Date, and Topics here...

if __name__ == "__main__":
    root = tk.Tk()
    app = IBPlannerApp(root)
    root.mainloop()
