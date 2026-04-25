from server.models import TaskInfo

TASK = TaskInfo(
    task_id="security_bugs-3",
    difficulty="security_bugs",
    description="Fix the ping command to avoid shell injection. Use a list of arguments and shell=False.",
    buggy_code="""import subprocess
def ping_host(host):
    return subprocess.check_output(f"ping -c 1 {host}", shell=True)""",
    test_code="""
import unittest
import inspect
class TestSecurity3(unittest.TestCase):
    def test_security(self):
        source = inspect.getsource(ping_host)
        self.assertNotIn("shell=True", source.replace(" ", ""))
        self.assertIn("[", source)
""",
    optimal_time_seconds=0.05
)
