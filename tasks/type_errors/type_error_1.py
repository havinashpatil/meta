from server.models import TaskInfo

TASK = TaskInfo(
    task_id="type_errors-1",
    difficulty="type_errors",
    description="Fix the function to sum a list of numbers that might be passed as strings. It currently tries to add int and str.",
    buggy_code="""def sum_all(items):
    total = 0
    for item in items:
        total = total + item
    return total""",
    test_code="""
import unittest
class TestTypeError1(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(sum_all([1, 2, 3]), 6)
    def test_strings(self):
        self.assertEqual(sum_all(['1', '2', '3']), 6)
    def test_mixed(self):
        self.assertEqual(sum_all([1, '2', 3]), 6)
""",
    optimal_time_seconds=0.05
)
