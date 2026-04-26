from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class CodeArenaObservation(BaseModel):
    buggy_code: str
    error_log: str
    test_results: str
    previous_attempts: List[str]
    
class CodeArenaAction(BaseModel):
    proposed_fix: Optional[str] = None
    action: Optional[str] = None

class TaskInfo(BaseModel):
    task_id: str
    difficulty: str
    description: str
    buggy_code: str
    test_code: str
    optimal_time_seconds: float
    
class ExecutionResult(BaseModel):
    compile_success: bool
    runtime_errors: str
    test_passed: int
    test_total: int
    execution_time_seconds: float
    success: bool
