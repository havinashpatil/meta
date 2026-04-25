from server.models import TaskInfo

TASK = TaskInfo(
    task_id="type_errors-2",
    difficulty="type_errors",
    description="Fix the function to count frequencies. It incorrectly calls .append() on a dict.",
    buggy_code="""def count_frequencies(words):
    counts = {}
    for word in words:
        if word not in counts:
            counts.append({word: 1})
        else:
            counts[word] += 1
    return counts""",
    test_code="""
import unittest
class TestTypeError2(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(count_frequencies(['apple', 'banana', 'apple']), {'apple': 2, 'banana': 1})
    def test_empty(self):
        self.assertEqual(count_frequencies([]), {})
""",
    optimal_time_seconds=0.05
)
