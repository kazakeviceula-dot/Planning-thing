import tkinter as tk
from tkinter import ttk, messagebox
from models import StudyManager, Test

class IBPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ula's IB Workload Manager")
        self.root.geometry("1000x700")
        
        self.manager = StudyManager()
        self.manager.load_from_json() # Load persisted state on startup

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.tab_dashboard = ttk.Frame(self.notebook)
        self.tab_tests = ttk.Frame(self.notebook)
        self.tab_availability = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_dashboard, text="Tab 1: Dashboard")
        self.notebook.add(self.tab_tests, text="Tab 2: Tests and Topics")
        self.notebook.add(self.tab_availability, text="Tab 3: Availability")

        self.build_test_tab()
        self.build_availability_tab()
        self.build_dashboard_tab()
        
        self.refresh_exam_list()

    # --- TAB 2: TESTS AND TOPICS ---
    def build_test_tab(self):
        ttk.Label(self.tab_tests, text="Add New Assessment", font=("Segoe UI", 14, "bold")).pack(pady=10)

        form = ttk.Frame(self.tab_tests)
        form.pack(pady=5)

        ttk.Label(form, text="Subject Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_subject = ttk.Entry(form, width=30)
        self.entry_subject.grid(row=0, column=1, pady=5)

        ttk.Label(form, text="Due Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_date = ttk.Entry(form, width=30)
        self.entry_date.grid(row=1, column=1, pady=5)

        ttk.Label(form, text="Topics (comma separated):").grid(row=2, column=0, sticky="w", pady=5)
        self.entry_topics = ttk.Entry(form, width=30)
        self.entry_topics.grid(row=2, column=1, pady=5)

       # Difficulty slider row with dynamic label
        ttk.Label(form, text="Difficulty Weight (1-10):").grid(row=3, column=0, sticky="w", pady=5)
        
        slider_frame = ttk.Frame(form)
        slider_frame.grid(row=3, column=1, sticky="ew", pady=5)

        self.scale_diff = ttk.Scale(slider_frame, from_=1, to=10, orient="horizontal", command=self.update_diff_label)
        self.scale_diff.set(5)
        self.scale_diff.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.lbl_diff_val = ttk.Label(slider_frame, text="5", font=("Segoe UI", 9, "bold"), width=3)
        self.lbl_diff_val.pack(side="right")

        ttk.Button(self.tab_tests, text="Add Test", command=self.save_test_input).pack(pady=10)

        ttk.Separator(self.tab_tests, orient="horizontal").pack(fill="x", padx=20, pady=10)

        ttk.Label(self.tab_tests, text="Upcoming Exams Priority List", font=("Segoe UI", 12, "bold")).pack(pady=5)
        
        self.lst_exams = tk.Listbox(self.tab_tests, width=70, height=8)
        self.lst_exams.pack(pady=5)

        btn_frame = ttk.Frame(self.tab_tests)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Delete Selected Test", command=self.delete_selected_test).pack(side="left", padx=5)
    
    def update_diff_label(self, val):
        # Converts floating-point slider value to integer display
        self.lbl_diff_val.config(text=str(int(float(val))))
        
    def save_test_input(self):
        sub = self.entry_subject.get().strip()
        date_str = self.entry_date.get().strip()
        topics = [t.strip() for t in self.entry_topics.get().split(",") if t.strip()]
        diff = int(self.scale_diff.get())

        if not sub or not date_str or not topics:
            messagebox.showwarning("Input Error", "Please fill in all test fields.")
            return

        try:
            new_test = Test(sub, date_str, topics, difficulty_weight=diff)
            self.manager.add_test(new_test)
            self.manager.save_to_json()
            messagebox.showinfo("Success", f"Added {sub} assessment!")
            
            self.entry_subject.delete(0, tk.END)
            self.entry_date.delete(0, tk.END)
            self.entry_topics.delete(0, tk.END)
            self.scale_diff.set(5)
            self.lbl_diff_val.config(text="5")
            
            self.refresh_exam_list()
        except ValueError:
            messagebox.showerror("Format Error", "Use YYYY-MM-DD for the exam due date.")

    def delete_selected_test(self):
        selected = self.lst_exams.curselection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a test from the list to delete.")
            return
        
        idx = selected[0]
        self.manager.remove_test(idx)
        self.manager.save_to_json()
        self.refresh_exam_list()
        messagebox.showinfo("Updated", "Exam removed successfully.")

    def refresh_exam_list(self):
        self.lst_exams.delete(0, tk.END)
        # Sort display by priority (date proximity)
        sorted_tests = sorted(self.manager.all_tests, key=lambda t: t.due_date)
        for t in sorted_tests:
            self.lst_exams.insert(
                tk.END, 
                f"{t.subject} | Due: {t.due_date_str} | Required Study: {t.hours_required} hrs | Topics: {len(t.topics)}"
            )

    # --- TAB 3: AVAILABILITY ---
    def build_availability_tab(self):
        ttk.Label(self.tab_availability, text="Block Non-Academic Time", font=("Segoe UI", 14, "bold")).pack(pady=10)

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

        btn_box = ttk.Frame(self.tab_availability)
        btn_box.pack(pady=10)
        
        ttk.Button(btn_box, text="Block Time Slot", command=self.save_activity_input).pack(side="left", padx=5)
        ttk.Button(btn_box, text="Clear Selected Date", command=self.clear_date_input).pack(side="left", padx=5)

    def save_activity_input(self):
        d_str = self.entry_avail_date.get().strip()
        try:
            start_h = int(self.entry_start_h.get())
            end_h = int(self.entry_end_h.get())
            if start_h < 7 or end_h > 23 or start_h >= end_h:
                raise ValueError()
                
            self.manager.add_activity(d_str, start_h, end_h)
            self.manager.save_to_json()
            messagebox.showinfo("Success", f"Blocked {start_h}:00 - {end_h}:00 on {d_str}")
        except ValueError:
            messagebox.showerror("Error", "Enter valid start (7-22) and end (8-23) hours.")

    def clear_date_input(self):
        d_str = self.entry_avail_date.get().strip()
        if d_str in self.manager.days_dict:
            self.manager.clear_day_activities(d_str)
            self.manager.save_to_json()
            messagebox.showinfo("Cleared", f"Cleared non-academic blocks for {d_str}")
        else:
            messagebox.showwarning("Error", "Date not found in schedule records.")

    # --- TAB 1: DASHBOARD ---
    def build_dashboard_tab(self):
        ttk.Label(self.tab_dashboard, text="Study Plan Dashboard", font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        btn_frame = ttk.Frame(self.tab_dashboard)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame, text="Generate Schedule", command=self.generate_and_refresh).pack(side="left", padx=5)

        legend = ttk.Label(
            self.tab_dashboard, 
            text="Legend: White (0) = Free Time | Red (1) = Blocked Activity | Green (2) = Allocated Study Session"
        )
        legend.pack(pady=5)

        # Scrollable Frame Canvas for Dynamic Matrix Scaling
        self.canvas = tk.Canvas(self.tab_dashboard)
        self.scrollbar = ttk.Scrollbar(self.tab_dashboard, orient="vertical", command=self.canvas.yview)
        self.frame_calendar = ttk.Frame(self.canvas)

        self.frame_calendar.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.frame_calendar, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        self.scrollbar.pack(side="right", fill="y")

    def generate_and_refresh(self):
        # Execute allocation algorithm and collect overflow warnings
        warnings = self.manager.distribute_study()
        self.manager.save_to_json()

        if warnings:
            messagebox.showwarning("Schedule Overflow Alert", "\n".join(warnings))

        for widget in self.frame_calendar.winfo_children():
            widget.destroy()

        dates = sorted(list(self.manager.days_dict.keys()))
        if not dates:
            ttk.Label(self.frame_calendar, text="No dates or availability set up yet.").pack()
            return

        # Render 16-slot time header (07:00 to 22:00)
        ttk.Label(self.frame_calendar, text="Date / Hour", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=4, pady=4)
        for h in range(16):
            ttk.Label(self.frame_calendar, text=f"{h+7:02d}:00", font=("Segoe UI", 8)).grid(row=0, column=h+1, padx=2, pady=2)

        # Dynamic Grid Drawing
        for r_idx, date_str in enumerate(dates):
            ttk.Label(self.frame_calendar, text=date_str, font=("Segoe UI", 9, "bold")).grid(row=r_idx+1, column=0, padx=4, pady=4)
            slots = self.manager.days_dict[date_str]
            for c_idx, state in enumerate(slots):
                color = "white" if state == 0 else "#ff9999" if state == 1 else "#99ff99"
                lbl = tk.Label(self.frame_calendar, text=str(state), bg=color, width=4, relief="solid", bd=1)
                lbl.grid(row=r_idx+1, column=c_idx+1, padx=1, pady=1)

if __name__ == "__main__":
    root = tk.Tk()
    app = IBPlannerApp(root)
    root.mainloop()
