import httpx


code = """#include <stdio.h>

int main() {
    int n, tq;
    printf("Enter number of processes: ");
    scanf("%d", &n);
    return 0;
}
"""

b = "http://127.0.0.1:7860"
httpx.post(f"{b}/reset", json={"task_id": "easy-1"}, timeout=30)
s = httpx.post(f"{b}/step", json={"proposed_fix": code}, timeout=60).json()
print(
    {
        "reward": s.get("reward"),
        "done": s.get("done"),
        "error_log": s.get("observation", {}).get("error_log", "")[:240],
        "test_results": s.get("observation", {}).get("test_results", ""),
    }
)
