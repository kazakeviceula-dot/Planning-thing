import unittest
import os
import tempfile
from datetime import datetime, timedelta
from models import Test, StudyManager

def day(offset):
    return (datetime.now().date() + timedelta(days=offset)).strftime("%Y-%m-%d")

class TestPlanner(unittest.TestCase):

    def setUp(self):
        # fresh manager before every test
        self.m = StudyManager()

    # T-01 Normal allocation
    def test_T01_normal_allocation(self):
        t = Test("Math HL", day(5), ["Derivatives", "Integration"], 3)
        self.m.add_test(t)
        self.m.ensure_date_range_for_tests()
        warnings = self.m.distribute_study()

        self.assertEqual(warnings, [])
        count = 0
        for d, slots in self.m.days_dict.items():
            n = slots.count("Math HL")
            count += n
            if d >= day(5):                    # nothing on/after the due date
                self.assertEqual(n, 0)
        self.assertEqual(count, 2)

    # T-02 Activity blocking
    def test_T02_activity_blocking(self):
        self.m.add_activity(day(0), 14, 16)
        self.assertEqual(self.m.days_dict[day(0)][7], 1)
        self.assertEqual(self.m.days_dict[day(0)][8], 1)

        self.m.add_test(Test("Math HL", day(3), ["A", "B", "C"], 9))
        self.m.ensure_date_range_for_tests()
        self.m.distribute_study()
        self.assertEqual(self.m.days_dict[day(0)][7], 1)   # still blocked
        self.assertEqual(self.m.days_dict[day(0)][8], 1)

    # T-03 Schedule overflow
    def test_T03_overflow(self):
        topics = [f"Topic{i}" for i in range(10)]
        self.m.add_test(Test("Computer Science A3 Networks", day(1), topics, 9))
        self.m.ensure_date_range_for_tests()
        warnings = self.m.distribute_study()        # must not crash

        self.assertEqual(len(warnings), 1)
        self.assertIn("Schedule Overflow", warnings[0])
        self.assertIn("14 more slot(s)", warnings[0])   # 30 needed - 16 available

    # T-04 Data persistence
    def test_T04_persistence(self):
        self.m.add_test(Test("Math HL", day(5), ["A", "B"], 3))
        self.m.add_test(Test("English", day(7), ["X"], 5))
        self.m.add_activity(day(1), 17, 19)
        self.m.ensure_date_range_for_tests()
        self.m.distribute_study()

        path = os.path.join(tempfile.gettempdir(), "test_schedule.json")
        self.m.save_to_json(path)

        loaded = StudyManager()
        loaded.load_from_json(path)
        os.remove(path)

        self.assertEqual([t.subject for t in loaded.all_tests],
                         [t.subject for t in self.m.all_tests])
        self.assertEqual(loaded.days_dict, self.m.days_dict)

    # T-05 Topic completion
    def test_T05_topic_completion(self):
        t = Test("Math HL", day(5), ["Derivatives", "Integration"], 3)
        self.m.add_test(t)
        self.assertEqual(t.hours_required, 2)

        t.toggle_topic("Derivatives")
        self.assertEqual(t.hours_required, 1)

        self.m.ensure_date_range_for_tests()
        self.m.distribute_study()
        total = sum(s.count("Math HL") for s in self.m.days_dict.values())
        self.assertEqual(total, 1)                  # excess slot freed

    # Input validation (model-level)
    def test_invalid_date_format(self):
        with self.assertRaises(ValueError):
            Test("Math", "2026/04/15", ["A"], 5)

if __name__ == "__main__":
    unittest.main(verbosity=2)
