from server.models import TaskInfo

TASK = TaskInfo(
    task_id="security_bugs-2",
    difficulty="security_bugs",
    description="Remove the hardcoded secret token and load it from the os.environ dictionary as 'API_TOKEN'.",
    buggy_code="""import os
def get_api_token():
    token = "secret_12345"
    return token""",
    test_code="""
import unittest
import inspect
import os
class TestSecurity2(unittest.TestCase):
    def test_normal(self):
        os.environ['API_TOKEN'] = 'my_secure_token'
        self.assertEqual(get_api_token(), 'my_secure_token')
    def test_security(self):
        source = inspect.getsource(get_api_token)
        self.assertNotIn("secret_12345", source)
""",
    optimal_time_seconds=0.05
)
