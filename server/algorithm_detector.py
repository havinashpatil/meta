"""
CodeArena Algorithm Detector
Classifies problem type from code/description + detects time complexity inefficiency.
Used to steer the AI fixer toward optimal algorithm selection.
"""

import re

# ── Problem Pattern Mapping ───────────────────────────────────────────────────

PATTERNS = {
    "max_subarray":   ["max subarray", "largest sum contiguous", "maximum sum", "kadane", "max_subarray"],
    "binary_search":  ["sorted array", "binary search", "binary_search", "search sorted", "log n"],
    "two_sum":        ["two sum", "pair sum", "two_sum", "find pair", "target sum"],
    "duplicate":      ["duplicate", "unique", "find duplicate", "repeated element"],
    "sorting":        ["sort", "bubble sort", "insertion sort", "selection sort", "arrange"],
    "sliding_window": ["sliding window", "substring", "subarray of length k", "window size"],
    "prefix_sum":     ["prefix sum", "range sum", "cumulative sum", "subarray sum"],
    "graph":          ["graph", "bfs", "dfs", "shortest path", "connected", "adjacency"],
    "dp":             ["dynamic programming", "memoization", "fibonacci", "knapsack", "longest"],
}

ALGO_HINTS = {
    "max_subarray":   "Use Kadane's Algorithm O(n): curr = max(num, curr+num); max_sum = max(max_sum, curr)",
    "binary_search":  "Use binary search O(log n): while low <= high: mid = (low+high)//2",
    "two_sum":        "Use hashmap O(n): seen = {}; if target-num in seen: return [seen[target-num], i]",
    "duplicate":      "Use set O(n): seen = set(); if num in seen: return num; seen.add(num)",
    "sorting":        "Use built-in sorted() O(n log n): return sorted(arr)",
    "sliding_window": "Use two pointers O(n): expand right, shrink left when constraint violated",
    "prefix_sum":     "Use prefix sum O(n): prefix[i] = prefix[i-1] + arr[i]",
    "graph":          "Use BFS/DFS O(V+E): collections.deque for BFS, recursion for DFS",
    "dp":             "Use memoization O(n): @lru_cache or dp table to store subproblems",
    "unknown":        "Analyze loops — if nested, consider prefix sum or hash map to reduce complexity",
}

# ── Detectors ─────────────────────────────────────────────────────────────────

def detect_problem_type(text: str) -> str:
    """Classify the problem type from code or description text."""
    text = text.lower()
    for key, keywords in PATTERNS.items():
        if any(k in text for k in keywords):
            return key
    return "unknown"


def detect_complexity(code: str) -> str:
    """
    Estimate time complexity by counting loop nesting depth.
    """
    lines = code.split('\n')
    max_depth = 0
    current_depth = 0

    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if re.match(r'^(for|while)\s', stripped):
            # Estimate nesting level by indent level (4 spaces = 1 level)
            depth = indent // 4 + 1
            max_depth = max(max_depth, depth)

    if max_depth >= 3:
        return "O(n^3)"
    elif max_depth == 2:
        return "O(n^2)"
    elif max_depth == 1:
        return "O(n)"
    return "O(1)"


def needs_optimization(code: str) -> bool:
    """Returns True if the code is worse than O(n log n)."""
    complexity = detect_complexity(code)
    return complexity in ["O(n^2)", "O(n^3)"]


def get_optimization_hint(code: str, description: str = "") -> str:
    """
    Full analysis: detect problem type + complexity + return targeted hint.
    """
    problem_type = detect_problem_type(description + " " + code)
    complexity = detect_complexity(code)
    hint = ALGO_HINTS.get(problem_type, ALGO_HINTS["unknown"])
    return f"Detected: {problem_type.replace('_', ' ').title()} | Current: {complexity} | Fix: {hint}"


def build_adaptive_prompt_suffix(reward: float) -> str:
    """
    Return adaptive prompting suffix based on current reward level.
    Steers model toward correctness, logic, or performance based on progress.
    """
    if reward < 0.4:
        return "\nFocus on correctness. Fix syntax errors and make sure all tests pass first."
    elif reward < 0.7:
        return "\nFix edge cases and logic bugs. Ensure the algorithm handles all inputs correctly."
    else:
        return "\nOptimize for performance. Reduce time complexity. Use O(n) algorithms where possible."
