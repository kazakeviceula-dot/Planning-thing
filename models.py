import json #used to save and load the schedule as a .json file
import os # used to check that the save file exists before loading it 
from datetime import datetime, timedelta # datetime converts text to dates, timedelta adds days/weeks to a date

# Always save/load next to this script, no matter where the program is launched from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "schedule.json")


# Test class: holds all the information about one singular assesment (subject, due date, topics, workload)
class Test:
    def __init__(self, subject: str, due_date: str, topics: list, difficulty_weight: int = 5, completed_topics: list = None):
        self.subject = subject
        self.due_date_str = due_date # text version (YYY-MM-DD), used for saving to JSOn and showing on screen 
        self.due_date = datetime.strptime(due_date, "%Y-%m-%d").date() # real date object, used for sorting and comparing, triggers ValueError if format is wrong
        self.topics = topics
        # if no list is given, create a new empty one (avoid all Test objects sharing the same list)
        self.completed_topics = completed_topics if completed_topics is not None else []
        self.difficulty_weight = int(difficulty_weight) # forces a whole number (1 to 10)
        self.update_hours_required() # work out the study hours straight away 

    # Amount hours dedicated based on workload: uncompleted topics x hours per topic
    # Hours per topcic : difficulty // 3 (whole-number division), never less than 1
    def update_hours_required(self):
        remaining_topics = [t for t in self.topics if t not in self.completed_topics] # keep only topics that are not yet ticked off 
        self.hours_required = len(remaining_topics) * max(1, self.difficulty_weight // 3)

    #Tick/untick a topic: if it is already completed remove it, otherwise add it, recalculate the hours accordingly
    def toggle_topic(self, topic: str):
        if topic in self.completed_topics:
            self.completed_topics.remove(topic)
        else:
            self.completed_topics.append(topic)
        self.update_hours_required()

    # Number of days left until the test 
    def days_until(self) -> int:
        return (self.due_date - datetime.now().date()).days

    # Convers the object into a plain dictionary so json can save it 
    # hours_required is not saved it is recaluclated when the test is loaded 
    def to_dict(self):
        return {
            "subject": self.subject,
            "due_date": self.due_date_str,
            "topics": self.topics,
            "completed_topics": self.completed_topics,
            "difficulty_weight": self.difficulty_weight
        }

    # Rebuilds a Test object from a saved dictionary 
    # .get(key, default) uses a given default value (5) if the key is missing from the file to prevent crashig
    @staticmethod
    def from_dict(data):
        return Test(
            data["subject"],
            data["due_date"],
            data["topics"],
            data.get("difficulty_weight", 5),
            data.get("completed_topics", [])
        )

# StudyManager works as a controller. Stores all tests and the calendar, as well as builds the study plan
class StudyManager:
    def __init__(self):
        self.all_tests = []# list of Test objects
        self.days_dict = {}# {"2026-11-03": [16 slots], ...}
        # Slot index = hour - 7, so index 0 is 07:00 and  index 15 is 22:00 (last hours ends at 23:00, after time study time is blocked)

    def add_test(self, test_obj: Test):
        self.all_tests.append(test_obj)

    #Removes a test at a given position in the list 
    def remove_test(self, index: int):
        if 0 <= index < len(self.all_tests):
            self.all_tests.pop(index)

    # Creates an empty day (16 slots), only if that date does not exist yet
    def init_day(self, date_str: str):
        if date_str not in self.days_dict:
            self.days_dict[date_str] = [0] * 16

    #Creates empty days starting from today 
    def generate_date_range(self, days_ahead: int = 14):
        today = datetime.now().date()
        for i in range(days_ahead):
            d_str = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            self.init_day(d_str)

    # Blocks time for a non-academic activity on one day 
    def add_activity(self, date_str: str, start_hour: int, end_hour: int):
        self.init_day(date_str)
        start_idx = max(0, start_hour - 7)
        end_idx = min(16, end_hour - 7)
        for i in range(start_idx, end_idx):
            self.days_dict[date_str][i] = 1

    # Blocks the same time on a weekday for several weeks ahead
    def add_recurring_activity(self, day_of_week: str, start_hour: int, end_hour: int, weeks_ahead: int = 4):
        days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
        target_weekday = days_map.get(day_of_week)
        if target_weekday is None:
            return

        today = datetime.now().date()
        days_ahead = (target_weekday - today.weekday()) % 7 
        first_date = today + timedelta(days=days_ahead)

        for week in range(weeks_ahead):
            current_date = first_date + timedelta(weeks=week)
            date_str = current_date.strftime("%Y-%m-%d")
            self.add_activity(date_str, start_hour, end_hour)

    # Makes sure that calendar covers today up to the last due date (minimum 14 days), making the calendar dynamic
    def ensure_date_range_for_tests(self, min_days=14):
        today = datetime.now().date()
        max_date = today + timedelta(days=min_days)

        for test in self.all_tests:
            if hasattr(test, 'due_date') and test.due_date > max_date:
                max_date = test.due_date

        curr = today
        while curr <= max_date:
            d_str = curr.strftime("%Y-%m-%d")
            if d_str not in self.days_dict:
                self.days_dict[d_str] = [0] * 16
            curr += timedelta(days=1)

    # Resets one day to all free
    def clear_day_activities(self, date_str: str):
        if date_str in self.days_dict:
            self.days_dict[date_str] = [0] * 16

    # Algorithm which fills free slots with study hours, most urgent tests first
    # Returns a list of overflow warnings 
    def distribute_study(self) -> list:
        # Erases old study slots (a slot that has a subject name), keeps blocked slots
        # Prevents duplicates when user presses regenerate plan
        for d_str in self.days_dict:
            self.days_dict[d_str] = [0 if slot not in (0, 1) else slot for slot in self.days_dict[d_str]]

        # Sorts tests b due date so the nearest test is scheduled first 
        sorted_tests = sorted(self.all_tests, key=lambda t: t.due_date)
        overflow_warnings = []

        for test in sorted_tests:
            needed_slots = test.hours_required

            # Goes through the days in the date order (YYYY-MM-DD)
            for date_str in sorted(self.days_dict.keys()): #chronological 
                if needed_slots == 0:  # all hours for this test are placed, stop scanning the remaining dates
                    break                

                slot_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if slot_date >= test.due_date: # never study on/after the test day
                    continue

                slots = self.days_dict[date_str]
                for idx in range(len(slots)):
                    if slots[idx] == 0 and needed_slots > 0:
                        slots[idx] = test.subject
                        needed_slots -= 1
           
            # If hours are left over there was not enough free time, so a warning is triggered 
            if needed_slots > 0:
                overflow_warnings.append(
                    f"Schedule Overflow: '{test.subject}' needs {needed_slots} more slot(s) before {test.due_date_str}!"
                )

        return overflow_warnings

    # Saves all tests and the whole calendar to schedule.json
    def save_to_json(self, filepath: str = SAVE_FILE):
        data = {
            "all_tests": [t.to_dict() for t in self.all_tests], # each Test becomes a dictionary
            "days_dict": self.days_dict
        }
        with open(filepath, "w") as f: # write
            json.dump(data, f, indent=4) # makes the file readable

    # Loads saved data when the program starts 
    def load_from_json(self, filepath: str = SAVE_FILE):
        if os.path.exists(filepath):
            with open(filepath, "r") as f: # read
                data = json.load(f)
                self.all_tests = [Test.from_dict(t) for t in data.get("all_tests", [])] # rebuild Test objects
                self.days_dict = data.get("days_dict", {})
        self.ensure_date_range_for_tests() # runs without a file, so the first launch still contains 14 days
