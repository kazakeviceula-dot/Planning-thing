import json
import os
from datetime import datetime, timedelta

class Test:
    def __init__(self, subject: str, due_date: str, topics: list, difficulty_weight: int = 5, completed_topics: list = None):
        self.subject = subject
        self.due_date_str = due_date
        self.due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        self.topics = topics
        self.completed_topics = completed_topics if completed_topics is not None else []
        self.difficulty_weight = int(difficulty_weight)
        self.update_hours_required()

    def update_hours_required(self):
        remaining_topics = [t for t in self.topics if t not in self.completed_topics]
        self.hours_required = len(remaining_topics) * max(1, self.difficulty_weight // 3)

    def toggle_topic(self, topic: str):
        if topic in self.completed_topics:
            self.completed_topics.remove(topic)
        else:
            self.completed_topics.append(topic)
        self.update_hours_required()

    def days_until(self) -> int:
        return (self.due_date - datetime.now().date()).days

    def to_dict(self):
        return {
            "subject": self.subject,
            "due_date": self.due_date_str,
            "topics": self.topics,
            "completed_topics": self.completed_topics,
            "difficulty_weight": self.difficulty_weight
        }

    @staticmethod
    def from_dict(data):
        return Test(
            data["subject"],
            data["due_date"],
            data["topics"],
            data.get("difficulty_weight", 5),
            data.get("completed_topics", [])
        )


class StudyManager:
    def __init__(self):
        self.all_tests = []
        self.days_dict = {}

    def add_test(self, test_obj: Test):
        self.all_tests.append(test_obj)

    def remove_test(self, index: int):
        if 0 <= index < len(self.all_tests):
            self.all_tests.pop(index)

    def init_day(self, date_str: str):
        if date_str not in self.days_dict:
            self.days_dict[date_str] = [0] * 16

    def generate_date_range(self, days_ahead: int = 14):
        today = datetime.now().date()
        for i in range(days_ahead):
            d_str = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            self.init_day(d_str)

    def add_activity(self, date_str: str, start_hour: int, end_hour: int):
        self.init_day(date_str)
        start_idx = max(0, start_hour - 7)
        end_idx = min(16, end_hour - 7)
        for i in range(start_idx, end_idx):
            self.days_dict[date_str][i] = 1

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

    def clear_day_activities(self, date_str: str):
        if date_str in self.days_dict:
            self.days_dict[date_str] = [0] * 16

    def distribute_study(self) -> list:
        for d_str in self.days_dict:
            self.days_dict[d_str] = [0 if slot not in (0, 1) else slot for slot in self.days_dict[d_str]]

        sorted_tests = sorted(self.all_tests, key=lambda t: t.due_date)
        overflow_warnings = []

        for test in sorted_tests:
            needed_slots = test.hours_required

            for date_str in sorted(self.days_dict.keys()):
                slot_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if slot_date >= test.due_date:
                    continue

                slots = self.days_dict[date_str]
                for idx in range(len(slots)):
                    if slots[idx] == 0 and needed_slots > 0:
                        slots[idx] = test.subject
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
        self.ensure_date_range_for_tests()
