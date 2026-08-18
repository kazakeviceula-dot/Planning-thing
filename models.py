import json
import os
from datetime import datetime

class Test:
    def __init__(self, subject: str, due_date: str, topics: list, difficulty_weight: int = 5):
        self.subject = subject
        self.due_date_str = due_date
        self.due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        self.topics = topics
        self.difficulty_weight = int(difficulty_weight)
        # Calculates required study slots based on topic count & difficulty
        self.hours_required = len(topics) * max(1, self.difficulty_weight // 3)

    def days_until(self) -> int:
        return (self.due_date - datetime.now().date()).days

    def to_dict(self):
        return {
            "subject": self.subject,
            "due_date": self.due_date_str,
            "topics": self.topics,
            "difficulty_weight": self.difficulty_weight
        }

    @staticmethod
    def from_dict(data):
        return Test(
            data["subject"],
            data["due_date"],
            data["topics"],
            data.get("difficulty_weight", 5)
        )


class StudyManager:
    def __init__(self):
        self.all_tests = []
        # days_dict structure: {"YYYY-MM-DD": [16 integer slots representing 07:00-23:00]}
        # 0 = Available, 1 = Occupied (Activity/Sleep hard limit), 2 = Allocated Study
        self.days_dict = {}

    def add_test(self, test_obj: Test):
        self.all_tests.append(test_obj)

    def remove_test(self, index: int):
        if 0 <= index < len(self.all_tests):
            self.all_tests.pop(index)

    def init_day(self, date_str: str):
        if date_str not in self.days_dict:
            self.days_dict[date_str] = [0] * 16

    def add_activity(self, date_str: str, start_hour: int, end_hour: int):
        self.init_day(date_str)
        # Hard limits constraint checking: 07:00 to 23:00 (16 slots total)
        start_idx = max(0, start_hour - 7)
        end_idx = min(16, end_hour - 7)
        for i in range(start_idx, end_idx):
            self.days_dict[date_str][i] = 1
            
    def add_recurring_activity(self, day_of_week: str, start_hour: int, end_hour: int, weeks_ahead: int = 4):
        """Blocks time slots for a specific day of the week across future weeks."""
        days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
        target_weekday = days_map.get(day_of_week)
        if target_weekday is None:
            return

        today = datetime.now().date()
        # Find next occurrence of the target day
        days_ahead = (target_weekday - today.weekday()) % 7
        first_date = today + timedelta(days=days_ahead)

        for week in range(weeks_ahead):
            current_date = first_date + timedelta(weeks=week)
            date_str = current_date.strftime("%Y-%m-%d")
            self.add_activity(date_str, start_hour, end_hour)


    def clear_day_activities(self, date_str: str):
        if date_str in self.days_dict:
            self.days_dict[date_str] = [0] * 16

    def distribute_study(self) -> list:
        """
        Chronological sorting and study allocation engine.
        Returns a list of warning messages for any overflowing tests.
        """
        # Reset all allocated study slots (2) back to available (0) before running
        for d_str in self.days_dict:
            self.days_dict[d_str] = [0 if slot == 2 else slot for slot in self.days_dict[d_str]]

        # Sort tests chronologically by due date (Urgency Priority Queue)
        sorted_tests = sorted(self.all_tests, key=lambda t: t.due_date)
        overflow_warnings = []

        for test in sorted_tests:
            needed_slots = test.hours_required
            
            # Linear search through available calendar days
            for date_str in sorted(self.days_dict.keys()):
                slot_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                # Do not allocate study time on or after the test date
                if slot_date >= test.due_date:
                    continue
                
                slots = self.days_dict[date_str]
                for idx in range(len(slots)):
                    if slots[idx] == 0 and needed_slots > 0:
                        slots[idx] = 2
                        needed_slots -= 1

            if needed_slots > 0:
                overflow_warnings.append(
                    f"Schedule Overflow: '{test.subject}' needs {needed_slots} more slot(s) before {test.due_date_str}!"
                )

        return overflow_warnings

    def save_to_json(self, filepath: str = "schedule.json"):
        data = {
            "all_tests": [t.to_dict() for t in self.all_tests],
            "days_dict": self.days_dict
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

    def load_from_json(self, filepath: str = "schedule.json"):
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                data = json.load(f)
                self.all_tests = [Test.from_dict(t) for t in data.get("all_tests", [])]
                self.days_dict = data.get("days_dict", {})
