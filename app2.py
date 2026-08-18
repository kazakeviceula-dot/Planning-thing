import tkinter as tk
from tkinter import ttk, messagebox
from models import StudyManager, Test

class IBPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ula's IB Workload Manager")
        self.root.geometry("950x650")
        self.manager = StudyManager()

        # Create Tab Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Tab Frames
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.tab_tests = ttk.Frame(self.notebook)
        self.tab_availability = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_dashboard, text="Tab 1: Dashboard")
        self.notebook.add(self.tab_tests, text="Tab 2: Tests and Topics")
        self.notebook.add(self.tab_availability, text="Tab 3: Availability")

        # Build Tab Content
        self.build_test_tab()
        self.build_availability_tab()
        self.build_dashboard_tab()

    # --- TAB 2: TESTS AND TOPICS ---
    def build_test_tab(self):
        ttk.Label(self.tab_tests, text="Add New Exam", font=("Arial", 14, "bold")).pack(pady=10)

        form = ttk.Frame(self.tab_tests)
        form.pack(pady=10)

        ttk.Label(form, text="Subject Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_subject = ttk.Entry(form, width=30)
        self.entry_subject.grid(row=0, column=1, pady=5)

        ttk.Label(form, text="Due Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_date = ttk.Entry(form, width=30)
        self.entry_date.grid(row=1, column=1, pady=5)

        ttk.Label(form, text="Topics (comma separated):").grid(row=2, column=0, sticky="w", pady=5)
        self.entry_topics = ttk.Entry(form, width=30)
        self.entry_topics.grid(row=2, column=1, pady=5)

        ttk.Button(self.tab_tests, text="Add Test", command=self.save_test_input).pack(pady=10)

        # List display for added exams
        ttk.Label(self.tab_tests, text="Upcoming Exams", font=("Arial", 12, "bold")).pack(pady=5)
        self.lbl_exams = ttk.Label(self.tab_tests, text="No exams added yet.")
        self.lbl_exams.pack()

    def save_test_input(self):
        sub = self.entry_subject.get().strip()
        date_str = self.entry_date.get().strip()
        topics = [t.strip() for t in self.entry_topics.get().split(",") if t.strip()]

        if not sub or not date_str or not topics:
            messagebox.showwarning("Error", "Please fill in all fields.")
            return

        try:
            new_test = Test(sub, date_str, topics)
            self.manager.add_test(new_test)
            messagebox.showinfo("Success", f"Added {sub} exam!")
            
            # Clear inputs
            self.entry_subject.delete(0, tk.END)
            self.entry_date.delete(0, tk.END)
            self.entry_topics.delete(0, tk.END)
            
            # Update exam list label
            exam_text = "\n".join([f"• {t.subject} (Due: {t.due_date})" for t in self.manager.all_tests])
            self.lbl_exams.config(text=exam_text)
        except ValueError:
            messagebox.showerror("Format Error", "Use YYYY-MM-DD for the date.")

    # --- TAB 3: AVAILABILITY MANAGER ---
    def build_availability_tab(self):
        ttk.Label(self.tab_availability, text="Block Non-Academic Time", font=("Arial", 14, "bold")).pack(pady=10)

        form = ttk.Frame(self.tab_availability)
        form.pack(pady=10)

        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_avail_date = ttk.Entry(form, width=25)
        self.entry_avail_date.grid(row=0, column=1, pady=5)

        ttk.Label(form, text="Start Hour (7-22):").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_start_h = ttk.Entry(form, width=25)
        self.entry_start_h.grid(row=1, column=1, pady=5)

        ttk.Label(form, text="End Hour (8-23):").grid(row=2, column=0, sticky="w", pady=5)
        self.entry_end_h = ttk.Entry(form, width=25)
        self.entry_end_h.grid(row=2, column=1, pady=5)

        ttk.Button(self.tab_availability, text="Block Time Slot", command=self.save_activity_input).pack(pady=10)

    def save_activity_input(self):
        d_str = self.entry_avail_date.get().strip()
        try:
            start_h = int(self.entry_start_h.get())
            end_h = int(self.entry_end_h.get())
            self.manager.add_activity(d_str, start_h, end_h)
            messagebox.showinfo("Success", f"Blocked {start_h}:00 - {end_h}:00 on {d_str}")
        except ValueError:
            messagebox.showerror("Error", "Enter valid integers for start and end hours.")

    # --- TAB 1: DASHBOARD & CALENDAR GRID ---
    def build_dashboard_tab(self):
        ttk.Label(self.tab_dashboard, text="Study Plan Dashboard", font=("Arial", 14, "bold")).pack(pady=10)
        
        btn_frame = ttk.Frame(self.tab_dashboard)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame, text="Generate Schedule", command=self.generate_and_refresh).pack(side="left", padx=5)

        # Legend
        legend = ttk.Label(self.tab_dashboard, text="Legend: White = Available (0) | Red = Occupied (1) | Green = Allocated Study (2)")
        legend.pack(pady=5)

        # Calendar Display Area
        self.frame_calendar = ttk.Frame(self.tab_dashboard)
        self.frame_calendar.pack(fill="both", expand=True, padx=20, pady=10)

    def generate_and_refresh(self):
        # Run allocation algorithm
        self.manager.distribute_study()
        
        # Clear existing grid
        for widget in self.frame_calendar.winfo_children():
            widget.destroy()

        # Build dynamic grid table
        dates = list(self.manager.days_dict.keys())
        if not dates:
            ttk.Label(self.frame_calendar, text="No dates or activities setup yet.").pack()
            return

        # Headers (Hours 07:00 to 22:00)
        ttk.Label(self.frame_calendar, text="Date / Hour", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=2, pady=2)
        for h in range(16):
            ttk.Label(self.frame_calendar, text=f"{h+7:02d}:00", font=("Arial", 8)).grid(row=0, column=h+1, padx=2, pady=2)

        # Rows for each registered day
        for r_idx, date_str in enumerate(dates):
            ttk.Label(self.frame_calendar, text=date_str, font=("Arial", 9, "bold")).grid(row=r_idx+1, column=0, padx=2, pady=2)
            slots = self.manager.days_dict[date_str]
            for c_idx, state in enumerate(slots):
                # State 0 = Available, State 1 = Occupied, State 2 = Allocated
                color = "white" if state == 0 else "#ff9999" if state == 1 else "#99ff99"
                lbl = tk.Label(self.frame_calendar, text=str(state), bg=color, width=4, relief="solid", bd=1)
                lbl.grid(row=r_idx+1, column=c_idx+1, padx=1, pady=1)

if __name__ == "__main__":
    root = tk.Tk()
    app = IBPlannerApp(root)
    root.mainloop()
