from datetime import datetime

class Test:
    def __init__(self, subject: str, due_date: str, topics: list, difficulty_weight: int = 5):
        self.subject = subject
        self.due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        self.topics = topics
        self.difficulty_weight = difficulty_weight
        # 1 slot per topic base, adjusted by difficulty
        self.hours_required = len(topics) * max(1, difficulty_weight // 3)

    def days_until(self) -> int:
        return (self.due_date - datetime.now().date()).days

class StudyManager:
    def __init__(self):
        self.all_tests = []
        # Key: "YYYY-MM-DD", Value: list of 16 slots (0=Available, 1=Occupied, 2=Allocated)
        self.days_dict = {}

    def add_test(self, test_obj: Test):
        self.all_tests.append(test_obj)

    def init_day(self, date_str: str):
        if date_str not in self.days_dict:
            # 16 time slots representing 07:00 to 23:00
            self.days_dict[date_str] = [0] * 16

    def add_activity(self, date_str: str, start_hour: int, end_hour: int):
        """Blocks time slots between 7 AM and 11 PM (07:00=idx 0, 22:00=idx 15)"""
        self.init_day(date_str)
        start_idx = max(0, start_hour - 7)
        end_idx = min(16, end_hour - 7)
        for i in range(start_idx, end_idx):
            self.days_dict[date_str][i] = 1 # Mark Occupied

def distribute_study(self):
        # Sort tests by urgency (earliest due date first)
        sorted_tests = sorted(self.all_tests, key=lambda t: t.due_date)
        
        for test in sorted_tests:
            needed_slots = test.hours_required
            # Attempt to allocate slots across available days
            for date_str, slots in self.days_dict.items():
                slot_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if slot_date >= test.due_date:
                    continue  # Stop if date is past test deadline
                
                for idx in range(len(slots)):
                    if slots[idx] == 0 and needed_slots > 0:
                        slots[idx] = 2 # Mark Allocated
                        needed_slots -= 1
            
            if needed_slots > 0:
                print(f"Warning: Schedule Overflow for {test.subject}!")
