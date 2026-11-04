import os
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from models import StudyManager, Test

# Ensure schedule.json and fonts always save/load right next to this script file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "schedule.json")

# Load Babell Bold font file into Windows memory session
FONT_PATH = os.path.join(BASE_DIR, "Babell Bold.ttf")
if os.path.exists(FONT_PATH):
    ctypes.windll.gdi32.AddFontResourceExW(FONT_PATH, 0x10, 0)

class IBPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ula's IB Workload Manager")
        self.root.geometry("1180x880")

        # Palette, including darker pastel blue/indigo theme
        self.BG_MAIN = "#8DA3F7"        
        self.BG_CARD = "#9FB1FB"        
        self.COLOR_PRIMARY = "#0045B2" 
        self.COLOR_ACCENT = "#FCFCD4"  
        self.COLOR_TEXT = "#000000"

        self.root.configure(bg=self.BG_MAIN)

        # Typography with Babell Bold applied to main headers and titles
        self.font_title = ("Babell Bold", 26)
        self.font_header = ("Babell Bold", 16)
        self.font_body = ("Georgia", 10)
        self.font_bold = ("Georgia", 10, "bold")

        # Initializing the backend controller (StudyManager), trying to load any saved data from last run of the program; if none exists, start fresh
        self.manager = StudyManager()
        try:
            self.manager.load_from_json()
        except Exception as e:
            print("Load failed:", e)
        
        # Ensure a 14-day minimum date range is created in memory 
        self.manager.ensure_date_range_for_tests(min_days=14)

        self.setup_styles()

        # Set up a multi-tab interface layout using ttk.Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=20)

        self.tab_dashboard = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_tests = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_availability = ttk.Frame(self.notebook, style="Card.TFrame")

        self.notebook.add(self.tab_dashboard, text=" Dashboard ")
        self.notebook.add(self.tab_tests, text=" Tests & Topics ")
        self.notebook.add(self.tab_availability, text=" Availability ")

        # Build individual tab UI components and details
        self.build_test_tab()
        self.build_availability_tab()
        self.build_dashboard_tab()

        self.refresh_exam_list()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Card.TFrame", background=self.BG_CARD)

        style.configure("TNotebook", background=self.BG_MAIN, borderwidth=0)
        style.configure("TNotebook.Tab", font=("Babell Bold", 12), padding=[16, 8], background=self.BG_MAIN, foreground=self.COLOR_PRIMARY)
        style.map("TNotebook.Tab", background=[("selected", self.BG_CARD)], foreground=[("selected", self.COLOR_PRIMARY)])

        style.configure("Header.TLabel", font=self.font_title, background=self.BG_CARD, foreground=self.COLOR_PRIMARY)
        style.configure("SubHeader.TLabel", font=self.font_header, background=self.BG_CARD, foreground=self.COLOR_PRIMARY)
        style.configure("TLabel", font=self.font_body, background=self.BG_CARD, foreground=self.COLOR_TEXT)

        style.configure("Primary.TButton", font=("Georgia", 11, "bold"), background=self.COLOR_PRIMARY, foreground="white", borderwidth=0, padding=8)
        style.map("Primary.TButton", background=[("active", "#003282")])

        style.configure("Accent.TButton", font=("Georgia", 10, "bold"), background=self.COLOR_ACCENT, foreground=self.COLOR_PRIMARY, borderwidth=1, padding=6)
        style.map("Accent.TButton", background=[("active", "#eaeaa6")])

        style.configure("TLabelframe", background=self.BG_CARD, borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", font=self.font_header, background=self.BG_CARD, foreground=self.COLOR_PRIMARY)

    # Handles input forms for assessments, priority listbox rendering, and dynamic topic progress checkboxes
    def build_test_tab(self):
        ttk.Label(self.tab_tests, text="ADD NEW ASSESSMENT", style="Header.TLabel").pack(pady=(20, 10))

        form = ttk.Frame(self.tab_tests, style="Card.TFrame")
        form.pack(pady=10, padx=20)

        # Subject Name input entry 
        ttk.Label(form, text="Subject Name:").grid(row=0, column=0, sticky="w", pady=8, padx=5)
        self.entry_subject = ttk.Entry(form, width=32, font=self.font_body)
        self.entry_subject.grid(row=0, column=1, pady=8, padx=5)

        # Due Date input entry (YYYY-MM-DD format)
        ttk.Label(form, text="Due Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", pady=8, padx=5)
        self.entry_date = ttk.Entry(form, width=32, font=self.font_body)
        self.entry_date.grid(row=1, column=1, pady=8, padx=5)

        # Renders a label and single-line text entry field for capturing topics as a comma-separated string
        ttk.Label(form, text="Topics (comma separated):").grid(row=2, column=0, sticky="w", pady=8, padx=5)
        self.entry_topics = ttk.Entry(form, width=32, font=self.font_body)
        self.entry_topics.grid(row=2, column=1, pady=8, padx=5)    

        # Difficulty Weight slider (from 1 to 10 scale)
        ttk.Label(form, text="Difficulty Weight (1-10):").grid(row=3, column=0, sticky="w", pady=8, padx=5)
        slider_frame = ttk.Frame(form, style="Card.TFrame")
        slider_frame.grid(row=3, column=1, sticky="ew", pady=8, padx=5)

        # The callback is attached AFTER the label exists, otherwise .set(5) fires it too early
        self.scale_diff = ttk.Scale(slider_frame, from_=1, to=10)
        self.scale_diff.set(5)
        self.scale_diff.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.lbl_diff_val = ttk.Label(slider_frame, text="5", font=self.font_bold, width=3)
        self.lbl_diff_val.pack(side="right")

        self.scale_diff.configure(command=self.update_diff_label)

        # Save button, which first checks if the user's input is valid, and then creates a new data object (e.g. Test) from that input 
        ttk.Button(self.tab_tests, text="Add Test", style="Primary.TButton", command=self.save_test_input).pack(pady=12)
        ttk.Separator(self.tab_tests, orient="horizontal").pack(fill="x", expand=True, padx=20, pady=15)

        ttk.Label(self.tab_tests, text="Upcoming Exams Priority List", style="SubHeader.TLabel").pack(pady=5)

        # Listbox displaying exams sorted by urgency/due date
        self.lst_exams = tk.Listbox(
            self.tab_tests, width=90, height=4, font=self.font_body, 
            bg="#FFFFFF", fg=self.COLOR_PRIMARY, selectbackground=self.COLOR_ACCENT, selectforeground=self.COLOR_PRIMARY, bd=1
        )
        self.lst_exams.pack(pady=8)
        self.lst_exams.bind("<<ListboxSelect>>", self.on_test_select)

        btn_frame = ttk.Frame(self.tab_tests, style="Card.TFrame")
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Delete Selected Test", style="Accent.TButton", command=self.delete_selected_test).pack()

        ttk.Separator(self.tab_tests, orient="horizontal").pack(fill="x", expand=True, padx=20, pady=15)

        # Container frame for dynamic topic completion checklists
        self.frame_topics = ttk.LabelFrame(self.tab_tests, text=" TOPIC COMPLETION TRACKER ")
        self.frame_topics.pack(fill="x", padx=20, pady=10)

    def update_diff_label(self, val):
        self.lbl_diff_val.config(text=str(int(float(val))))


    # Validates typing, saves the new exam, clears form, and calls refresh_exam_list
    # (ignoree this comment)
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

            # Clear form fields after successful save
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
            return

        # The listbox is sorted by date, so look up the test in the same sorted order
        sorted_tests = sorted(self.manager.all_tests, key=lambda t: t.due_date)
        self.manager.all_tests.remove(sorted_tests[selected[0]])
        self.manager.save_to_json()
        self.refresh_exam_list()

        for w in self.frame_topics.winfo_children():
            w.destroy()

    # Sorts all the user's exams by due date and updates the main listbox text with the latest progress
    def refresh_exam_list(self):
        self.lst_exams.delete(0, tk.END)
        sorted_tests = sorted(self.manager.all_tests, key=lambda t: t.due_date)
        for t in sorted_tests:
            completed_cnt = len(t.completed_topics)
            total_cnt = len(t.topics)
            self.lst_exams.insert(
                tk.END,
                f"  {t.subject}  |  Due: {t.due_date_str}  |  Hours Needed: {t.hours_required} hrs  |  Progress: {completed_cnt}/{total_cnt} Topics"
            )

    # Listens for when the user clicks an exam in that list, clears out old checkboxes, and builds new interactive checkboxes for that specific exam's topics
    def on_test_select(self, event):
        selected = self.lst_exams.curselection()
        if not selected:
            return

        sorted_tests = sorted(self.manager.all_tests, key=lambda t: t.due_date)
        test = sorted_tests[selected[0]]

        for w in self.frame_topics.winfo_children():
            w.destroy()

        self.frame_topics.config(text=f" TOPIC COMPLETION TRACKER: {test.subject.upper()} ")

        for topic in test.topics:
            var = tk.BooleanVar(value=(topic in test.completed_topics))
            chk = ttk.Checkbutton(
                self.frame_topics,
                text=f"  {topic}",
                variable=var,
                command=lambda t=test, top=topic: self.toggle_topic_status(t, top)
            )
            chk.pack(anchor="w", padx=15, pady=4)

    # Fires instantly whenever a user clicks a checkbox, updates completion progress, saves to JSON, and refreshes the list
    def toggle_topic_status(self, test, topic):
        test.toggle_topic(topic)
        self.manager.save_to_json()
        self.refresh_exam_list()

    # Captures single-date and recurring extracurricular time blocks (setting matrix values to 1)
    def build_availability_tab(self):
        ttk.Label(self.tab_availability, text="BLOCK NON-ACADEMIC TIME", style="Header.TLabel").pack(pady=(20, 10))

        # Single date block form frame (a visual container box which groups related input fields under a single title)
        frame_single = ttk.LabelFrame(self.tab_availability, text=" SINGLE DATE TIME BLOCK ")
        frame_single.pack(fill="x", padx=30, pady=10)

        ttk.Label(frame_single, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", padx=8, pady=10)
        self.entry_avail_date = ttk.Entry(frame_single, width=15, font=self.font_body)
        self.entry_avail_date.grid(row=0, column=1, padx=8, pady=10)

        ttk.Label(frame_single, text="Start Hour (7-22):").grid(row=0, column=2, sticky="w", padx=8, pady=10)
        self.entry_start_h = ttk.Entry(frame_single, width=8, font=self.font_body)
        self.entry_start_h.grid(row=0, column=3, padx=8, pady=10)

        ttk.Label(frame_single, text="End Hour (8-23):").grid(row=0, column=4, sticky="w", padx=8, pady=10)
        self.entry_end_h = ttk.Entry(frame_single, width=8, font=self.font_body)
        self.entry_end_h.grid(row=0, column=5, padx=8, pady=10)

        ttk.Button(frame_single, text="Block Date", style="Primary.TButton", command=self.save_activity_input).grid(row=0, column=6, padx=15, pady=10)

        # Recurring weekly activity form frame
        frame_recur = ttk.LabelFrame(self.tab_availability, text=" RECURRING WEEKLY ACTIVITY ")
        frame_recur.pack(fill="x", padx=30, pady=15)

        ttk.Label(frame_recur, text="Day of Week:").grid(row=0, column=0, sticky="w", padx=8, pady=10)
        self.combo_dow = ttk.Combobox(
            frame_recur,
            values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            width=12,
            font=self.font_body
        )
        self.combo_dow.current(0)
        self.combo_dow.grid(row=0, column=1, padx=8, pady=10)

        ttk.Label(frame_recur, text="Start Hour (7-22):").grid(row=0, column=2, sticky="w", padx=8, pady=10)
        self.entry_rec_start = ttk.Entry(frame_recur, width=8, font=self.font_body)
        self.entry_rec_start.grid(row=0, column=3, padx=8, pady=10)

        ttk.Label(frame_recur, text="End Hour (8-23):").grid(row=0, column=4, sticky="w", padx=8, pady=10)
        self.entry_rec_end = ttk.Entry(frame_recur, width=8, font=self.font_body)
        self.entry_rec_end.grid(row=0, column=5, padx=8, pady=10)

        ttk.Button(frame_recur, text="Block Recurring Day", style="Primary.TButton", command=self.save_recurring_input).grid(row=0, column=6, padx=15, pady=10)

        frame_clear = ttk.Frame(self.tab_availability, style="Card.TFrame")
        frame_clear.pack(pady=15)
        ttk.Button(frame_clear, text="Clear Selected Date Blocks", style="Accent.TButton", command=self.clear_date_input).pack()

    def save_activity_input(self):
        d_str = self.entry_avail_date.get().strip()
        try:
            datetime.strptime(d_str, "%Y-%m-%d")

            start_h = int(self.entry_start_h.get())
            end_h = int(self.entry_end_h.get())
            if start_h < 7 or end_h > 23 or start_h >= end_h:
                raise ValueError()

            self.manager.add_activity(d_str, start_h, end_h)
            self.manager.save_to_json()
            messagebox.showinfo("Success", f"Blocked {start_h}:00 - {end_h}:00 on {d_str}")
        except ValueError:
            messagebox.showerror("Error", "Enter a valid date (YYYY-MM-DD) and hours (7-23).")

    def save_recurring_input(self):
        dow = self.combo_dow.get()
        try:
            start_h = int(self.entry_rec_start.get())
            end_h = int(self.entry_rec_end.get())
            if start_h < 7 or end_h > 23 or start_h >= end_h:
                raise ValueError()

            self.manager.add_recurring_activity(dow, start_h, end_h)
            self.manager.save_to_json()
            messagebox.showinfo("Success", f"Blocked every {dow} {start_h}:00 - {end_h}:00!")
        except ValueError:
            messagebox.showerror("Error", "Enter valid hours.")

    def clear_date_input(self):
        d_str = self.entry_avail_date.get().strip()
        if d_str in self.manager.days_dict:
            self.manager.clear_day_activities(d_str)
            self.manager.save_to_json()
            messagebox.showinfo("Cleared", f"Cleared blocks for {d_str}")

    # Renders the scrollable color-coded calendar matrix (White = Free, Red = Blocked, Blue = Allocated Subject)
    def build_dashboard_tab(self):
        ttk.Label(self.tab_dashboard, text="STUDY PLAN DASHBOARD", style="Header.TLabel").pack(pady=(20, 10))

        btn_frame = ttk.Frame(self.tab_dashboard, style="Card.TFrame")
        btn_frame.pack(pady=10)

        # Button to trigger the scheduling algorithm 
        ttk.Button(btn_frame, text="Generate Schedule", style="Primary.TButton", command=self.generate_and_refresh).pack()

        # Visual color legend for the calendar 
        legend_frame = tk.Frame(self.tab_dashboard, bg=self.BG_MAIN)
        legend_frame.pack(pady=10)

        tk.Label(legend_frame, text="Legend: ", font=("Babell Bold", 12), fg=self.COLOR_PRIMARY, bg=self.BG_MAIN).pack(side="left")
        tk.Label(legend_frame, text=" Free ", font=("Georgia", 10, "bold"), bg="#FFFFFF", fg="#000000", bd=1, relief="solid").pack(side="left", padx=5)
        tk.Label(legend_frame, text=" Blocked Activity ", font=("Georgia", 10, "bold"), bg="#FF8989", fg="#FFFFFF", bd=1, relief="solid").pack(side="left", padx=5)
        tk.Label(legend_frame, text=" Study Slot ", font=("Georgia", 10, "bold"), bg="#0079D2", fg="#FFFFFF", bd=1, relief="solid").pack(side="left", padx=5)

        # Scrollable canvas setup for calendar display 
        self.canvas = tk.Canvas(self.tab_dashboard, bg="#FFFFFF")
        self.scrollbar = ttk.Scrollbar(self.tab_dashboard, orient="vertical", command=self.canvas.yview)
        self.frame_calendar = ttk.Frame(self.canvas, style="Card.TFrame")

        self.frame_calendar.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.frame_calendar, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        self.scrollbar.pack(side="right", fill="y", pady=10)

    def generate_and_refresh(self):
        warnings = self.manager.distribute_study()
        self.manager.save_to_json()

        if warnings:
            messagebox.showwarning("Overflow Alert", "\n".join(warnings))

        # Clears out any old calendar elements and looks up all saved dates in order; if no dates exist, a message pops up
        for widget in self.frame_calendar.winfo_children():
            widget.destroy()

        dates = sorted(list(self.manager.days_dict.keys()))
        if not dates:
            ttk.Label(self.frame_calendar, text="No dates or availability set up yet.").pack()
            return

        # Draw header row for hours (07:00 to 22:00)
        ttk.Label(self.frame_calendar, text="Date / Hour", font=self.font_bold).grid(row=0, column=0, padx=6, pady=6)
        for h in range(16):
            ttk.Label(self.frame_calendar, text=f"{h+7:02d}:00", font=("Georgia", 9, "bold")).grid(row=0, column=h+1, padx=3, pady=6)

        # Iterate through each date and render cell states (0 = Free, 1 = Blocked, String = Study)
        for r_idx, date_str in enumerate(dates):
            ttk.Label(self.frame_calendar, text=date_str, font=self.font_bold).grid(row=r_idx+1, column=0, padx=6, pady=4)
            slots = self.manager.days_dict[date_str]
            for c_idx, state in enumerate(slots):
                if state == 0:
                    color = "#FFFFFF"
                    text_color = "#888888"
                    display_text = "Free"
                elif state == 1:
                    color = "#FF8989"
                    text_color = "#FFFFFF"
                    display_text = "Blocked"
                else:
                    color = "#0079D2"
                    text_color = "#FFFFFF"
                    display_text = str(state)[:6]

                lbl = tk.Label(
                    self.frame_calendar,
                    text=display_text,
                    bg=color,
                    fg=text_color,
                    width=8,
                    font=("Georgia", 9, "bold" if state != 0 else "normal"),
                    bd=1,
                    relief="solid"
                )
                lbl.grid(row=r_idx+1, column=c_idx+1, padx=2, pady=2)

        self.frame_calendar.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

if __name__ == "__main__":
    root = tk.Tk()
    app = IBPlannerApp(root)
    root.mainloop()
