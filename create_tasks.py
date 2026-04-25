import os
import json

base_dir = "e:/meta/tasks"
os.makedirs(os.path.join(base_dir, "type_errors"), exist_ok=True)
os.makedirs(os.path.join(base_dir, "security_bugs"), exist_ok=True)

def write_task(folder, name, task_id, difficulty, desc, buggy, test):
    py_path = os.path.join(base_dir, folder, f"{name}.py")
    json_path = os.path.join(base_dir, folder, f"{name}.json")
    
    py_content = f'''from server.models import TaskInfo

TASK = TaskInfo(
    task_id="{task_id}",
    difficulty="{difficulty}",
    description="{desc}",
    buggy_code="""{buggy}""",
    test_code="""{test}""",
    optimal_time_seconds=0.05
)
'''
    with open(py_path, "w", encoding="utf-8") as f:
        f.write(py_content)
        
    json_content = {
        "task_id": task_id,
        "difficulty": difficulty,
        "description": desc,
        "buggy_code": buggy,
        "test_code": test,
        "optimal_time_seconds": 0.05
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_content, f, indent=2)


# Type Error 1
write_task("type_errors", "type_error_1", "type_errors-1", "type_errors",
    "Fix the function to sum a list of numbers that might be passed as strings. It currently tries to add int and str.",
    "def sum_all(items):\n    total = 0\n    for item in items:\n        total = total + item\n    return total",
    "\nimport unittest\nclass TestTypeError1(unittest.TestCase):\n    def test_normal(self):\n        self.assertEqual(sum_all([1, 2, 3]), 6)\n    def test_strings(self):\n        self.assertEqual(sum_all(['1', '2', '3']), 6)\n    def test_mixed(self):\n        self.assertEqual(sum_all([1, '2', 3]), 6)\n")

# Type Error 2
write_task("type_errors", "type_error_2", "type_errors-2", "type_errors",
    "Fix the function to count frequencies. It incorrectly calls .append() on a dict.",
    "def count_frequencies(words):\n    counts = {}\n    for word in words:\n        if word not in counts:\n            counts.append({word: 1})\n        else:\n            counts[word] += 1\n    return counts",
    "\nimport unittest\nclass TestTypeError2(unittest.TestCase):\n    def test_normal(self):\n        self.assertEqual(count_frequencies(['apple', 'banana', 'apple']), {'apple': 2, 'banana': 1})\n    def test_empty(self):\n        self.assertEqual(count_frequencies([]), {})\n")

# Type Error 3
write_task("type_errors", "type_error_3", "type_errors-3", "type_errors",
    "Fix the function to format names. It incorrectly calls .upper() on an int ID.",
    "def format_records(records):\n    formatted = []\n    for user_id, name in records:\n        formatted.append(f\"{user_id.upper()} - {name.upper()}\")\n    return formatted",
    "\nimport unittest\nclass TestTypeError3(unittest.TestCase):\n    def test_normal(self):\n        self.assertEqual(format_records([(1, 'alice'), (2, 'bob')]), ['1 - ALICE', '2 - BOB'])\n")


# Security Bug 1
write_task("security_bugs", "security_bug_1", "security_bugs-1", "security_bugs",
    "Fix the function to parse JSON safely without using eval().",
    "import json\ndef parse_user_data(data_string):\n    return eval(data_string)",
    "\nimport unittest\nimport inspect\nclass TestSecurity1(unittest.TestCase):\n    def test_normal(self):\n        self.assertEqual(parse_user_data('{\"name\": \"alice\"}'), {\"name\": \"alice\"})\n    def test_security(self):\n        source = inspect.getsource(parse_user_data)\n        self.assertNotIn(\"eval(\", source)\n")

# Security Bug 2
write_task("security_bugs", "security_bug_2", "security_bugs-2", "security_bugs",
    "Remove the hardcoded secret token and load it from the os.environ dictionary as 'API_TOKEN'.",
    "import os\ndef get_api_token():\n    token = \"secret_12345\"\n    return token",
    "\nimport unittest\nimport inspect\nimport os\nclass TestSecurity2(unittest.TestCase):\n    def test_normal(self):\n        os.environ['API_TOKEN'] = 'my_secure_token'\n        self.assertEqual(get_api_token(), 'my_secure_token')\n    def test_security(self):\n        source = inspect.getsource(get_api_token)\n        self.assertNotIn(\"secret_12345\", source)\n")

# Security Bug 3
write_task("security_bugs", "security_bug_3", "security_bugs-3", "security_bugs",
    "Fix the ping command to avoid shell injection. Use a list of arguments and shell=False.",
    "import subprocess\ndef ping_host(host):\n    return subprocess.check_output(f\"ping -c 1 {host}\", shell=True)",
    "\nimport unittest\nimport inspect\nclass TestSecurity3(unittest.TestCase):\n    def test_security(self):\n        source = inspect.getsource(ping_host)\n        self.assertNotIn(\"shell=True\", source.replace(\" \", \"\"))\n        self.assertIn(\"[\", source)\n")

# Rewrite __init__.py
init_content = """from .easy import EASY_TASK
from .medium import MEDIUM_TASK
from .hard import HARD_TASK
from .type_errors.type_error_1 import TASK as TE1
from .type_errors.type_error_2 import TASK as TE2
from .type_errors.type_error_3 import TASK as TE3
from .security_bugs.security_bug_1 import TASK as SB1
from .security_bugs.security_bug_2 import TASK as SB2
from .security_bugs.security_bug_3 import TASK as SB3

ALL_TASKS = [EASY_TASK, MEDIUM_TASK, HARD_TASK, TE1, TE2, TE3, SB1, SB2, SB3]
"""

with open(os.path.join(base_dir, "__init__.py"), "w", encoding="utf-8") as f:
    f.write(init_content)

print("Tasks generated successfully!")
