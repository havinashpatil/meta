/**
 * CodeArena API Service
 * Connects to the FastAPI backend at localhost:7860 (proxied via Vite).
 *
 * Real endpoint contracts (from server/app.py):
 *   POST /reset  →  { task_id }       →  { status, observation, info }
 *   POST /step   →  { proposed_fix }  →  { observation, reward, done, info }
 *   GET  /state  →                    →  { observation }
 */

const BASE = '';  // proxied through Vite — no prefix needed

// ─── Helpers ────────────────────────────────────────────────────

async function request(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);

  try {
    const res = await fetch(`${BASE}${url}`, {
      signal: controller.signal,
      ...options,
    });

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
    }

    return await res.json();
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error(`Request to ${url} timed out after 30s`);
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

function post(url, body) {
  return request(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// ─── Public API ─────────────────────────────────────────────────

/**
 * POST /reset
 * @param {string} taskId - "easy", "medium", "hard", "auto", or exact ID like "easy-1"
 * @returns {{ status, observation: { buggy_code, error_log, test_results, previous_attempts }, info: { task_id, difficulty } }}
 */
export async function resetTask(taskId = 'easy') {
  return post('/reset', { task_id: taskId });
}

/**
 * POST /step
 * @param {string} proposedFix - The code fix to submit
 * @returns {{ observation, reward: number, done: boolean, info: { execution_metadata, task_id, reward_components } }}
 */
export async function sendStep(proposedFix) {
  return post('/step', { proposed_fix: proposedFix });
}

/**
 * GET /state
 * @returns {{ observation: { buggy_code, error_log, test_results, previous_attempts } }}
 */
export async function getState() {
  return request('/state');
}

/**
 * GET / (health check)
 * @returns {{ status: "ok", environment: "CodeArena" }}
 */
export async function healthCheck() {
  return request('/health');
}

/**
 * POST /fix
 * Uses built-in pattern fixer + optional Ollama.
 * Passes reward + task_id for memory storage and adaptive prompting.
 * @param {string} code - Buggy code
 * @param {string} errorLog - Error output
 * @param {string} ollamaUrl - Ollama server URL
 * @param {string} model - Model name
 * @param {number} reward - Current reward (for adaptive prompting)
 * @param {string} taskId - Task ID (for memory retrieval)
 * @returns {{ fixed_code, method, success, explanation, complexity, algo_hint, note? }}
 */
export async function generateFix(code, errorLog = '', ollamaUrl = 'http://localhost:11434', model = 'llama3.2:latest', reward = 0.0, taskId = '') {
  return post('/fix', {
    code,
    error_log: errorLog,
    ollama_url: ollamaUrl,
    model,
    use_ollama: true,
    reward,
    task_id: taskId,
  });
}

/**
 * GET /stats
 * Returns complexity vs reward stats + episode history.
 */
export async function getStats() {
  return request('/stats');
}

/**
 * GET /memory
 * Returns all stored best solutions from agent memory.
 */
export async function getMemory() {
  return request('/memory');
}

/**
 * POST /run_raw
 * Sandbox mode: executes arbitrary code and returns stdout, stderr, and execution time complexity.
 * @param {string} code - The code to execute
 * @returns {{ status: "success"|"error", stdout: string, stderr: string, execution_time: number, time_complexity_hint: string, reward: number, reward_components: object, done: boolean }}
 */
export async function runRaw(code) {
  return post('/run_raw', { code });
}
