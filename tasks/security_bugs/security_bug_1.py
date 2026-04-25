from server.models import TaskInfo

TASK = TaskInfo(
    task_id="security_bugs-1",
    difficulty="security_bugs",
    description="Fix the function to parse JSON safely without using eval().",
    buggy_code="""import json
def parse_user_data(data_string):
    return eval(data_string)""",
    test_code="""
import unittest
import inspect
class TestSecurity1(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(parse_user_data('{"name": "alice"}'), {"name": "alice"})
    def test_security(self):
        source = inspect.getsource(parse_user_data)
        self.assertNotIn("eval(", source)
""",
    optimal_time_seconds=0.05
)
