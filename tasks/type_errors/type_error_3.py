from server.models import TaskInfo

TASK = TaskInfo(
    task_id="type_errors-3",
    difficulty="type_errors",
    description="Fix the function to format names. It incorrectly calls .upper() on an int ID.",
    buggy_code="""def format_records(records):
    formatted = []
    for user_id, name in records:
        formatted.append(f"{user_id.upper()} - {name.upper()}")
    return formatted""",
    test_code="""
import unittest
class TestTypeError3(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(format_records([(1, 'alice'), (2, 'bob')]), ['1 - ALICE', '2 - BOB'])
""",
    optimal_time_seconds=0.05
)
