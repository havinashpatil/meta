
import React, { useState, useEffect, useRef, useCallback } from "react";

/* ─────────────────────────────────────────────
   GOOGLE FONTS
───────────────────────────────────────────── */
const FontLoader = () => {
  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href =
      "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Rajdhani:wght@400;500;600;700&display=swap";
    document.head.appendChild(link);
    return () => document.head.removeChild(link);
  }, []);
  return null;
};

/* ─────────────────────────────────────────────
   GLOBAL STYLES
───────────────────────────────────────────── */
const GlobalStyles = () => (
  <style>{`
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #0a0e1a; color: #e2e8f0; font-family: 'Rajdhani', sans-serif; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0a0e1a; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #334155; }

    @keyframes pulse-border {
      0%,100%{box-shadow:0 0 0 0 rgba(0,255,136,0.4),inset 0 0 20px rgba(0,255,136,0.05);}
      50%{box-shadow:0 0 0 6px rgba(0,255,136,0),inset 0 0 30px rgba(0,255,136,0.12);}
    }
    @keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
    @keyframes slide-in-right{from{opacity:0;transform:translateX(30px)}to{opacity:1;transform:translateX(0)}}
    @keyframes success-glow{0%,100%{box-shadow:0 0 30px rgba(0,255,136,0.15)}50%{box-shadow:0 0 60px rgba(0,255,136,0.35)}}
    @keyframes spin{to{transform:rotate(360deg)}}
    @keyframes dot-pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.4;transform:scale(0.7)}}
    @keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
    @keyframes ticker{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}

    .thinking-border{animation:pulse-border 1.5s ease-in-out infinite;}
    .success-glow{animation:success-glow 2s ease-in-out infinite;}
    .blink{animation:blink 1s step-end infinite;}
    .fade-in{animation:fadeIn 0.3s ease both;}

    .code-block{
      font-family:'JetBrains Mono',monospace;font-size:12px;line-height:1.7;
      background:#0d1117;border:1px solid #1e293b;border-radius:8px;
      padding:14px;overflow:auto;color:#a8d8a8;white-space:pre;tab-size:4;
    }
    .terminal-block{
      font-family:'JetBrains Mono',monospace;font-size:11.5px;line-height:1.75;
      background:#050810;border:1px solid #1e293b;border-radius:8px;
      padding:14px;overflow:auto;white-space:pre-wrap;
    }
    .btn{
      font-family:'Rajdhani',sans-serif;font-weight:600;font-size:13px;
      letter-spacing:0.05em;border:none;border-radius:6px;cursor:pointer;
      padding:8px 18px;transition:all 0.18s ease;display:inline-flex;align-items:center;gap:6px;
    }
    .btn:disabled{opacity:0.4;cursor:not-allowed;}
    .btn-primary{background:linear-gradient(135deg,#00ff88 0%,#00c96f 100%);color:#0a0e1a;}
    .btn-primary:hover:not(:disabled){background:linear-gradient(135deg,#33ffaa 0%,#00e07a 100%);box-shadow:0 0 16px rgba(0,255,136,0.4);transform:translateY(-1px);}
    .btn-danger{background:linear-gradient(135deg,#ff4455 0%,#cc1122 100%);color:#fff;}
    .btn-danger:hover:not(:disabled){box-shadow:0 0 16px rgba(255,68,85,0.4);transform:translateY(-1px);}
    .btn-ghost{background:transparent;border:1px solid #1e293b;color:#94a3b8;}
    .btn-ghost:hover:not(:disabled){border-color:#334155;color:#e2e8f0;background:#111827;}
    .btn-amber{background:linear-gradient(135deg,#ffaa00 0%,#cc8800 100%);color:#0a0e1a;}
    .btn-amber:hover:not(:disabled){box-shadow:0 0 16px rgba(255,170,0,0.4);transform:translateY(-1px);}

    .panel{background:#111827;border:1px solid #1e293b;border-radius:12px;overflow:hidden;}
    .panel-header{
      background:#0d1117;border-bottom:1px solid #1e293b;padding:10px 16px;
      display:flex;align-items:center;gap:8px;font-family:'Rajdhani',sans-serif;
      font-weight:700;font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:#64748b;
    }
    .badge{font-size:10px;font-weight:700;letter-spacing:0.08em;padding:2px 8px;border-radius:4px;text-transform:uppercase;}
    .badge-easy{background:rgba(0,255,136,0.15);color:#00ff88;border:1px solid rgba(0,255,136,0.3);}
    .badge-medium{background:rgba(255,170,0,0.15);color:#ffaa00;border:1px solid rgba(255,170,0,0.3);}
    .badge-hard{background:rgba(255,68,85,0.15);color:#ff4455;border:1px solid rgba(255,68,85,0.3);}
    .badge-info{background:rgba(99,179,237,0.15);color:#63b3ed;border:1px solid rgba(99,179,237,0.3);}
    .badge-ollama{background:rgba(139,92,246,0.15);color:#a78bfa;border:1px solid rgba(139,92,246,0.3);}

    .task-btn{
      width:100%;text-align:left;background:#1a2235;border:1px solid #1e293b;
      border-radius:8px;padding:12px 14px;cursor:pointer;transition:all 0.18s ease;
      font-family:'Rajdhani',sans-serif;color:#e2e8f0;
    }
    .task-btn:hover{border-color:#334155;background:#1f2d45;}
    .task-btn.active{border-color:#00ff88;background:rgba(0,255,136,0.08);}
    .task-btn.active-medium{border-color:#ffaa00;background:rgba(255,170,0,0.08);}
    .task-btn.active-hard{border-color:#ff4455;background:rgba(255,68,85,0.08);}

    .stat-card{background:#1a2235;border:1px solid #1e293b;border-radius:8px;padding:10px 14px;}
    .reward-bar-outer{height:6px;background:#1e293b;border-radius:3px;overflow:hidden;margin-top:6px;}
    .reward-bar-inner{height:100%;border-radius:3px;transition:width 0.8s cubic-bezier(0.25,0.46,0.45,0.94);}
    .log-entry{
      background:#1a2235;border:1px solid #1e293b;border-radius:8px;
      padding:10px 12px;margin-bottom:8px;
      animation:slide-in-right 0.4s cubic-bezier(0.25,0.46,0.45,0.94) both;
    }
    .dot-live{width:8px;height:8px;border-radius:50%;background:#00ff88;animation:dot-pulse 1.5s ease-in-out infinite;display:inline-block;}
    .spinner{width:14px;height:14px;border:2px solid rgba(0,255,136,0.2);border-top-color:#00ff88;border-radius:50%;animation:spin 0.8s linear infinite;display:inline-block;}

    .cfg-input{
      width:100%;font-family:'JetBrains Mono',monospace;font-size:12px;
      background:#0d1117;border:1px solid #1e293b;border-radius:6px;
      color:#e2e8f0;padding:8px 12px;outline:none;letter-spacing:0.04em;
    }
    .cfg-input:focus{border-color:#a78bfa;}
    select.cfg-input{cursor:pointer;}
    textarea{
      font-family:'JetBrains Mono',monospace;font-size:12px;line-height:1.7;
      background:#0d1117;border:1px solid #1e293b;border-radius:8px;
      color:#a8d8a8;padding:14px;resize:vertical;outline:none;width:100%;
    }
    textarea:focus{border-color:#00ff88;box-shadow:0 0 0 2px rgba(0,255,136,0.15);}

    .status-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px;}
    .status-dot.online{background:#00ff88;box-shadow:0 0 6px rgba(0,255,136,0.5);}
    .status-dot.offline{background:#ff4455;box-shadow:0 0 6px rgba(255,68,85,0.5);}
    .status-dot.checking{background:#ffaa00;animation:dot-pulse 1s ease-in-out infinite;}
  `}</style>
);

/* ─────────────────────────────────────────────
   TASKS (mirrors server tasks — display only)
───────────────────────────────────────────── */
const TASKS = {
  "easy-1": {
    id: "easy-1", label: "Easy", name: "Fix average_list()", difficulty: "easy",
    description: "Fix syntax errors: missing colon after def and uses length() instead of len().",
    hints: ["Missing colon after def", "length() → len()"],
    buggy_code: `def average_list(numbers)\n    if length(numbers) == 0:\n        return 0\n    return sum(numbers) / length(numbers)`,
  },
  "medium-1": {
    id: "medium-1", label: "Medium", name: "Fix binary_search()", difficulty: "medium",
    description: "Fix logical bugs: loop condition skips last element; left pointer causes infinite loop.",
    hints: ["left < right → left <= right", "left = mid → left = mid + 1"],
    buggy_code: `def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left < right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid\n        else:\n            right = mid - 1\n    return -1`,
  },
  "hard-1": {
    id: "hard-1", label: "Hard", name: "Optimize max_subarray_sum()", difficulty: "hard",
    description: "Replace O(N³) brute-force with Kadane's O(N) algorithm.",
    hints: ["Use Kadane's algorithm", "Eliminate triple nested loop"],
    buggy_code: `def max_subarray_sum(arr):\n    if not arr:\n        return 0\n    max_sum = arr[0]\n    for i in range(len(arr)):\n        for j in range(i, len(arr)):\n            for k in range(i, j+1):\n                current = sum(arr[i:j+1])\n                if current > max_sum:\n                    max_sum = current\n    return max_sum`,
  },
};

/* ─────────────────────────────────────────────
   REWARD COLOR
───────────────────────────────────────────── */
function rewardColor(r) {
  if (r >= 0.85) return "#00ff88";
  if (r >= 0.5) return "#ffaa00";
  return "#ff4455";
}

/* ─────────────────────────────────────────────
   ANSI LINE RENDERER
───────────────────────────────────────────── */
function AnsiLine({ text }) {
  const parts = text.split(/\x1b\[(\d+)m/);
  let color = null;
  const els = [];
  parts.forEach((p, i) => {
    if (p === "32") color = "#00ff88";
    else if (p === "33") color = "#ffaa00";
    else if (p === "31") color = "#ff4455";
    else if (p === "0") color = null;
    else els.push(<span key={i} style={color ? { color } : {}}>{p}</span>);
  });
  return <span>{els}</span>;
}

/* ─────────────────────────────────────────────
   REWARD CHART
───────────────────────────────────────────── */
function RewardChart({ rewards }) {
  const W = 260, H = 100, PAD = 20;
  const pts = rewards.map((r, i) => ({
    x: PAD + (i / Math.max(4, 1)) * (W - PAD * 2),
    y: PAD + (1 - r) * (H - PAD * 2),
    r,
  }));
  const pathD = pts.length > 1 ? pts.reduce((a, p, i) => i === 0 ? `M${p.x},${p.y}` : a + ` L${p.x},${p.y}`, "") : "";
  const areaD = pts.length > 1 ? `${pathD} L${pts[pts.length - 1].x},${H - PAD} L${pts[0].x},${H - PAD} Z` : "";
  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`}>
      <defs>
        <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#00ff88" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#00ff88" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0, 0.5, 1].map(v => {
        const y = PAD + (1 - v) * (H - PAD * 2);
        return <line key={v} x1={PAD} y1={y} x2={W - PAD} y2={y} stroke="#1e293b" strokeWidth="1" strokeDasharray="3,3" />;
      })}
      {[1, 2, 3, 4, 5].map(s => (
        <text key={s} x={PAD + ((s - 1) / 4) * (W - PAD * 2)} y={H - 4}
          fill="#334155" fontSize="8" textAnchor="middle" fontFamily="JetBrains Mono">{s}</text>
      ))}
      {areaD && <path d={areaD} fill="url(#rg)" />}
      {pathD && <path d={pathD} fill="none" stroke="#00ff88" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />}
      {pts.map((p, i) => <circle key={i} cx={p.x} cy={p.y} r="4" fill="#0a0e1a" stroke={rewardColor(p.r)} strokeWidth="2" />)}
    </svg>
  );
}

/* ─────────────────────────────────────────────
   MAIN APP
───────────────────────────────────────────── */
export default function CodeArenaRL() {
  /* ── Ollama config ── */
  const [ollamaUrl, setOllamaUrl] = useState("http://localhost:11434");
  const [ollamaModel, setOllamaModel] = useState("codellama");
  const [availableModels, setAvailableModels] = useState([]);
  const [ollamaStatus, setOllamaStatus] = useState("checking"); // checking | online | offline

  /* ── OpenEnv (FastAPI) config ── */
  const [envUrl, setEnvUrl] = useState("http://localhost:7860");
  const [envStatus, setEnvStatus] = useState("checking");

  /* ── Task & episode state ── */
  const [selectedTask, setSelectedTask] = useState("easy-1");
  const [envState, setEnvState] = useState(null);   // observation from server
  const [uiMode, setUiMode] = useState("idle");      // idle|resetting|agent_thinking|executing|done
  const [episodeLog, setEpisodeLog] = useState([]);
  const [rewards, setRewards] = useState([]);
  const [stepCount, setStepCount] = useState(0);
  const [isDone, setIsDone] = useState(false);

  /* ── Code display ── */
  const [streamingCode, setStreamingCode] = useState("");
  const [agentCode, setAgentCode] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [execOutput, setExecOutput] = useState([]);  // lines from /step response

  /* ── Manual mode ── */
  const [manualMode, setManualMode] = useState(false);
  const [manualCode, setManualCode] = useState("");

  /* ── Speed ── */
  const [speed, setSpeed] = useState("normal");
  const speedMap = { slow: 3, normal: 1, fast: 0.25 };

  /* ── Misc ── */
  const [tokenEst, setTokenEst] = useState(0);
  const [collapsedEntries, setCollapsedEntries] = useState(new Set());
  const [copied, setCopied] = useState(false);
  const [errorBanner, setErrorBanner] = useState("");

  const runningRef = useRef(false);
  const logRef = useRef(null);
  const task = TASKS[selectedTask];

  /* ──────────────────────────────────────────
     STATUS PROBES
  ─────────────────────────────────────────── */
  const probeOllama = useCallback(async () => {
    setOllamaStatus("checking");
    try {
      const res = await fetch(`${ollamaUrl}/api/tags`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        const data = await res.json();
        const names = (data.models || []).map(m => m.name);
        setAvailableModels(names.length > 0 ? names : ["codellama", "llama3", "mistral", "deepseek-coder"]);
        setOllamaStatus("online");
      } else {
        setOllamaStatus("offline");
      }
    } catch {
      setOllamaStatus("offline");
      setAvailableModels(["codellama", "llama3", "mistral", "deepseek-coder"]);
    }
  }, [ollamaUrl]);

  const probeEnv = useCallback(async () => {
    setEnvStatus("checking");
    try {
      const res = await fetch(`${envUrl}/`, { signal: AbortSignal.timeout(3000) });
      setEnvStatus(res.ok ? "online" : "offline");
    } catch {
      setEnvStatus("offline");
    }
  }, [envUrl]);

  useEffect(() => { probeOllama(); }, [probeOllama]);
  useEffect(() => { probeEnv(); }, [probeEnv]);

  /* ──────────────────────────────────────────
     OPENENV API CALLS
  ─────────────────────────────────────────── */
  const envReset = useCallback(async (taskId) => {
    const res = await fetch(`${envUrl}/reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId }),
    });
    if (!res.ok) throw new Error(`/reset failed: ${res.status}`);
    const data = await res.json();
    return data.observation; // { buggy_code, error_log, test_results, previous_attempts }
  }, [envUrl]);

  const envStep = useCallback(async (proposedFix) => {
    const res = await fetch(`${envUrl}/step`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ proposed_fix: proposedFix }),
    });
    if (!res.ok) throw new Error(`/step failed: ${res.status}`);
    const data = await res.json();
    // { observation, reward, done, info }
    return data;
  }, [envUrl]);

  /* ──────────────────────────────────────────
     OLLAMA CALL
  ─────────────────────────────────────────── */
  const callOllama = useCallback(async (obs) => {
    const prompt = [
      `You are an expert Python debugging agent in a reinforcement learning environment.`,
      `Return ONLY the fixed Python code — no explanation, no markdown, no code fences.`,
      ``,
      `Task: ${task.description}`,
      ``,
      `BUGGY CODE:`,
      obs.buggy_code,
      ``,
      `ERROR LOG:`,
      obs.error_log || "No errors yet",
      ``,
      `TEST RESULTS:`,
      obs.test_results || "No tests run yet",
      ``,
      `PREVIOUS FAILED ATTEMPTS (${(obs.previous_attempts || []).length}):`,
      (obs.previous_attempts || []).length > 0
        ? obs.previous_attempts.join("\n---\n")
        : "None",
      ``,
      `Return ONLY the corrected Python code:`,
    ].join("\n");

    setTokenEst(Math.ceil(prompt.length / 4));

    const res = await fetch(`${ollamaUrl}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: ollamaModel,
        prompt,
        stream: false,
        options: { temperature: 0.2, num_predict: 512 },
      }),
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Ollama error ${res.status}: ${errText}`);
    }

    const data = await res.json();
    let code = (data.response || "").trim();

    // Strip markdown code fences if model adds them
    code = code.replace(/^```[\w]*\n?/gm, "").replace(/```\s*$/gm, "").trim();
    return code;
  }, [ollamaUrl, ollamaModel, task]);

  /* ──────────────────────────────────────────
     STREAM TEXT (typing animation)
  ─────────────────────────────────────────── */
  const streamText = useCallback((text, setter, onDone) => {
    const delay = Math.max(4, 18 * speedMap[speed]);
    let i = 0;
    setter("");
    setIsTyping(true);
    const iv = setInterval(() => {
      if (!runningRef.current) { clearInterval(iv); return; }
      i++;
      setter(text.slice(0, i));
      if (i >= text.length) { clearInterval(iv); setIsTyping(false); if (onDone) onDone(); }
    }, delay);
  }, [speed]);

  /* ──────────────────────────────────────────
     BUILD EXECUTION OUTPUT LINES from /step
  ─────────────────────────────────────────── */
  const buildOutputLines = (stepResp) => {
    const { reward, done, info, observation } = stepResp;
    const meta = info?.execution_metadata || {};
    const passed = meta.test_passed ?? "?";
    const total = meta.test_total ?? "?";
    const elapsed = (Math.random() * 0.003 + 0.001).toFixed(3);
    const errors = meta.runtime_errors || observation?.error_log || "";

    const lines = [];
    if (reward >= 0.99 || (passed !== "?" && passed >= total)) {
      lines.push(`\x1b[32m${"." .repeat(typeof total === "number" ? total : 3)}\x1b[0m`);
      lines.push(`----------------------------------------------------------------------`);
      lines.push(`Ran ${total} tests in ${elapsed}s`);
      lines.push(``);
      lines.push(`\x1b[32mOK\x1b[0m`);
    } else if (passed > 0) {
      const fail = total - passed;
      lines.push(`\x1b[33m${"F".repeat(fail)}${"." .repeat(passed)}\x1b[0m`);
      lines.push(``);
      lines.push(`FAIL: partial solution — ${fail} test(s) failed`);
      if (errors) lines.push(`RuntimeError: ${errors.split("\n")[0]}`);
      lines.push(`----------------------------------------------------------------------`);
      lines.push(`Ran ${total} tests in ${elapsed}s`);
      lines.push(``);
      lines.push(`\x1b[33mFAILED (failures=${fail})\x1b[0m`);
    } else {
      lines.push(`\x1b[31m${"F".repeat(typeof total === "number" ? total : 3)}\x1b[0m`);
      lines.push(``);
      if (errors) {
        errors.split("\n").slice(0, 3).forEach(l => lines.push(l));
      } else {
        lines.push(`FAIL: all tests failed`);
      }
      lines.push(`----------------------------------------------------------------------`);
      lines.push(`Ran ${total} tests in ${elapsed}s`);
      lines.push(``);
      lines.push(`\x1b[31mFAILED (errors=${typeof total === "number" ? total : "?"})\x1b[0m`);
    }
    return lines;
  };

  /* ──────────────────────────────────────────
     STREAM OUTPUT LINES
  ─────────────────────────────────────────── */
  const streamLines = useCallback((lines, onDone) => {
    const delay = Math.max(60, 180 * speedMap[speed]);
    let i = 0;
    setExecOutput([]);
    const iv = setInterval(() => {
      if (!runningRef.current) { clearInterval(iv); return; }
      i++;
      setExecOutput(lines.slice(0, i));
      if (i >= lines.length) { clearInterval(iv); if (onDone) onDone(); }
    }, delay);
  }, [speed]);

  /* ──────────────────────────────────────────
     RESET EPISODE
  ─────────────────────────────────────────── */
  const resetEpisode = useCallback(() => {
    runningRef.current = false;
    setEnvState(null); setUiMode("idle");
    setEpisodeLog([]); setRewards([]);
    setStepCount(0); setIsDone(false);
    setStreamingCode(""); setAgentCode("");
    setExecOutput([]); setIsTyping(false);
    setManualCode(""); setTokenEst(0);
    setCollapsedEntries(new Set());
    setErrorBanner("");
  }, []);

  /* ──────────────────────────────────────────
     RUN ONE STEP
  ─────────────────────────────────────────── */
  const runStep = useCallback(async (currentObs, currentStepCount) => {
    if (!runningRef.current) return;

    const mult = speedMap[speed];
    const interStepDelay = Math.max(400, 1200 * mult);

    /* 1. Agent thinking */
    setUiMode("agent_thinking");

    let fixedCode;
    try {
      fixedCode = manualMode
        ? (manualCode.trim() || currentObs.buggy_code)
        : await callOllama(currentObs);
    } catch (err) {
      if (!runningRef.current) return;
      setErrorBanner(`🦙 Ollama Error: ${err.message}`);
      setUiMode("idle");
      runningRef.current = false;
      return;
    }
    if (!runningRef.current) return;

    /* 2. Stream agent code */
    await new Promise(resolve => streamText(fixedCode, setStreamingCode, resolve));
    if (!runningRef.current) return;
    setAgentCode(fixedCode);

    /* 3. Call OpenEnv /step */
    setUiMode("executing");
    let stepResult;
    try {
      stepResult = await envStep(fixedCode);
    } catch (err) {
      if (!runningRef.current) return;
      setErrorBanner(`🌐 OpenEnv Error: ${err.message}`);
      setUiMode("idle");
      runningRef.current = false;
      return;
    }
    if (!runningRef.current) return;

    const { observation: newObs, reward, done } = stepResult;
    const meta = stepResult.info?.execution_metadata || {};
    const passed = meta.test_passed ?? 0;
    const total = meta.test_total ?? task.hints.length + 1;
    const newStep = currentStepCount + 1;

    /* 4. Stream execution output */
    const outputLines = buildOutputLines(stepResult);
    await new Promise(resolve => streamLines(outputLines, resolve));
    if (!runningRef.current) return;

    /* 5. Update state */
    setEnvState(newObs);
    setStepCount(newStep);
    setRewards(prev => [...prev, reward]);
    setIsDone(done);

    const logEntry = {
      step: newStep,
      code_submitted: fixedCode,
      reward, done, passed, total,
      error_log: newObs?.error_log || "",
      test_results: newObs?.test_results || "",
      timestamp: new Date().toISOString(),
    };
    setEpisodeLog(prev => [logEntry, ...prev]);

    /* 6. Done or continue */
    if (done) {
      setUiMode("done");
      runningRef.current = false;
      return;
    }

    /* Wait then continue */
    await new Promise(r => setTimeout(r, interStepDelay));
    if (!runningRef.current) return;
    runStep(newObs, newStep);
  }, [speed, manualMode, manualCode, callOllama, streamText, streamLines, envStep, task]);

  /* ──────────────────────────────────────────
     START EPISODE
  ─────────────────────────────────────────── */
  const startEpisode = useCallback(async () => {
    if (ollamaStatus !== "online" && !manualMode) {
      setErrorBanner("🦙 Ollama is offline. Start Ollama or enable Manual Mode.");
      return;
    }
    if (envStatus !== "online") {
      setErrorBanner("🌐 OpenEnv server is offline. Run: uvicorn server.app:app --port 7860");
      return;
    }

    resetEpisode();
    setErrorBanner("");

    await new Promise(r => setTimeout(r, 60));
    runningRef.current = true;
    setUiMode("resetting");

    let initialObs;
    try {
      initialObs = await envReset(selectedTask);
    } catch (err) {
      setErrorBanner(`🌐 OpenEnv /reset Error: ${err.message}`);
      setUiMode("idle");
      runningRef.current = false;
      return;
    }

    setEnvState(initialObs);
    setTimeout(() => runStep(initialObs, 0), 400);
  }, [ollamaStatus, envStatus, manualMode, resetEpisode, envReset, selectedTask, runStep]);

  /* ──────────────────────────────────────────
     COPY EPISODE JSON
  ─────────────────────────────────────────── */
  const copyJSON = useCallback(() => {
    const data = {
      task: selectedTask,
      model: ollamaModel,
      timestamp: new Date().toISOString(),
      total_steps: episodeLog.length,
      final_reward: rewards[rewards.length - 1] ?? 0,
      success: (rewards[rewards.length - 1] ?? 0) >= 0.99,
      episode_log: [...episodeLog].reverse(),
    };
    navigator.clipboard.writeText(JSON.stringify(data, null, 2)).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2200);
    });
  }, [selectedTask, ollamaModel, episodeLog, rewards]);

  useEffect(() => { if (logRef.current) logRef.current.scrollTop = 0; }, [episodeLog.length]);

  const totalReward = rewards.reduce((a, b) => a + b, 0);
  const finalReward = rewards[rewards.length - 1] ?? 0;
  const success = finalReward >= 0.99;
  const isRunning = ["agent_thinking", "executing", "resetting"].includes(uiMode);

  const termColor = line => {
    if (line.includes("OK")) return "#00ff88";
    if (line.includes("FAIL") || line.includes("Error") || line.includes("error")) return "#ff4455";
    if (line.includes("---") || line.includes("Ran")) return "#64748b";
    return "#94a3b8";
  };

  /* ──────────────────────────────────────────
     RENDER
  ─────────────────────────────────────────── */
  return (
    <>
      <FontLoader />
      <GlobalStyles />
      <div style={{ minHeight: "100vh", background: "#0a0e1a", display: "flex", flexDirection: "column" }}>

        {/* ── NAVBAR ── */}
        <nav style={{
          background: "#070b14", borderBottom: "1px solid #1e293b",
          padding: "0 24px", height: 54, display: "flex", alignItems: "center",
          justifyContent: "space-between", position: "sticky", top: 0, zIndex: 100,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ position: "relative" }}>
              <span style={{ fontFamily: "'Rajdhani',sans-serif", fontWeight: 700, fontSize: 20, letterSpacing: "0.06em", color: "#e2e8f0" }}>
                Code<span style={{ color: "#00ff88" }}>Arena</span>
                <span style={{ color: "#a78bfa" }}> RL</span>
              </span>
              <span className="dot-live" style={{ position: "absolute", top: 2, right: -12, width: 7, height: 7 }} />
            </div>
            <span className="badge badge-ollama" style={{ marginLeft: 4 }}>🦙 Ollama</span>
          </div>

          <div style={{ overflow: "hidden", flex: 1, margin: "0 32px", maxWidth: 360 }}>
            <div style={{ display: "flex", gap: 32, animation: "ticker 14s linear infinite", whiteSpace: "nowrap", fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: "#1e293b", letterSpacing: "0.08em" }}>
              {[...Array(4)].map((_, i) => <span key={i}>AGENT BENCHMARKING · PYTHON DEBUG · RL EVAL · OPENENV · OLLAMA · </span>)}
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {/* Live status pills */}
            <div style={{ fontSize: 11, fontFamily: "'JetBrains Mono',monospace", display: "flex", alignItems: "center", gap: 4, color: "#64748b" }}>
              <span className={`status-dot ${ollamaStatus}`} />
              Ollama
            </div>
            <div style={{ fontSize: 11, fontFamily: "'JetBrains Mono',monospace", display: "flex", alignItems: "center", gap: 4, color: "#64748b" }}>
              <span className={`status-dot ${envStatus}`} />
              OpenEnv
            </div>
            <span className="badge badge-info">Scaler SST 2025</span>
            <span className="badge" style={{ background: "rgba(139,92,246,0.15)", color: "#a78bfa", border: "1px solid rgba(139,92,246,0.3)" }}>
              Theme #3 · World Modeling
            </span>
          </div>
        </nav>

        {/* ── ERROR BANNER ── */}
        {errorBanner && (
          <div style={{
            background: "rgba(255,68,85,0.12)", borderBottom: "1px solid rgba(255,68,85,0.3)",
            padding: "10px 24px", fontFamily: "'JetBrains Mono',monospace", fontSize: 12,
            color: "#ff8899", display: "flex", justifyContent: "space-between", alignItems: "center",
          }}>
            {errorBanner}
            <button onClick={() => setErrorBanner("")} className="btn btn-ghost" style={{ fontSize: 11, padding: "2px 10px" }}>✕</button>
          </div>
        )}

        {/* ── MAIN GRID ── */}
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "25% 45% 30%", height: `calc(100vh - ${54 + (errorBanner ? 41 : 0)}px)`, overflow: "hidden" }}>

          {/* ════════════════════ LEFT PANEL ════════════════════ */}
          <div style={{ padding: "16px 14px", borderRight: "1px solid #1e293b", overflowY: "auto", display: "flex", flexDirection: "column", gap: 14 }}>

            {/* Ollama Config */}
            <div className="panel">
              <div className="panel-header">🦙 &nbsp;Ollama Config</div>
              <div style={{ padding: "12px 14px", display: "flex", flexDirection: "column", gap: 10 }}>
                <div>
                  <div style={{ fontSize: 10, color: "#64748b", marginBottom: 4, letterSpacing: "0.08em", textTransform: "uppercase" }}>Base URL</div>
                  <input className="cfg-input" value={ollamaUrl} onChange={e => setOllamaUrl(e.target.value)} placeholder="http://localhost:11434" />
                </div>
                <div>
                  <div style={{ fontSize: 10, color: "#64748b", marginBottom: 4, letterSpacing: "0.08em", textTransform: "uppercase" }}>Model</div>
                  {availableModels.length > 0 ? (
                    <select className="cfg-input" value={ollamaModel} onChange={e => setOllamaModel(e.target.value)}>
                      {availableModels.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                  ) : (
                    <input className="cfg-input" value={ollamaModel} onChange={e => setOllamaModel(e.target.value)} placeholder="codellama" />
                  )}
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  <button className="btn btn-ghost" style={{ flex: 1, justifyContent: "center", fontSize: 11 }} onClick={probeOllama}>
                    {ollamaStatus === "checking" ? <><span className="spinner" />Checking...</> : `↻ ${ollamaStatus === "online" ? "✓ Online" : "✗ Offline"}`}
                  </button>
                </div>
                {ollamaStatus === "offline" && (
                  <div style={{ fontSize: 10, color: "#ffaa00", fontFamily: "'JetBrains Mono',monospace", background: "rgba(255,170,0,0.08)", border: "1px solid rgba(255,170,0,0.2)", borderRadius: 4, padding: "6px 8px" }}>
                    💡 Run: <strong>ollama serve</strong><br />
                    Then pull a model:<br />
                    <strong>ollama pull codellama</strong>
                  </div>
                )}
              </div>
            </div>

            {/* OpenEnv Config */}
            <div className="panel">
              <div className="panel-header">🌐 &nbsp;OpenEnv Server</div>
              <div style={{ padding: "12px 14px", display: "flex", flexDirection: "column", gap: 10 }}>
                <div>
                  <div style={{ fontSize: 10, color: "#64748b", marginBottom: 4, letterSpacing: "0.08em", textTransform: "uppercase" }}>FastAPI URL</div>
                  <input className="cfg-input" value={envUrl} onChange={e => setEnvUrl(e.target.value)} placeholder="http://localhost:7860" />
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  <button className="btn btn-ghost" style={{ flex: 1, justifyContent: "center", fontSize: 11 }} onClick={probeEnv}>
                    {envStatus === "checking" ? <><span className="spinner" />Checking...</> : `↻ ${envStatus === "online" ? "✓ Online" : "✗ Offline"}`}
                  </button>
                </div>
                {envStatus === "offline" && (
                  <div style={{ fontSize: 10, color: "#ff8899", fontFamily: "'JetBrains Mono',monospace", background: "rgba(255,68,85,0.08)", border: "1px solid rgba(255,68,85,0.2)", borderRadius: 4, padding: "6px 8px" }}>
                    ⚠ Start server:<br />
                    <strong>uvicorn server.app:app --port 7860</strong>
                  </div>
                )}
              </div>
            </div>

            {/* Task Selector */}
            <div className="panel">
              <div className="panel-header">🎯 &nbsp;Select Task</div>
              <div style={{ padding: "12px 14px", display: "flex", flexDirection: "column", gap: 8 }}>
                {Object.values(TASKS).map(t => {
                  const isActive = selectedTask === t.id;
                  const ac = t.difficulty === "easy" ? "active" : t.difficulty === "medium" ? "active-medium" : "active-hard";
                  return (
                    <button key={t.id} className={`task-btn ${isActive ? ac : ""}`} disabled={isRunning}
                      onClick={() => { setSelectedTask(t.id); resetEpisode(); }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                        <span style={{ fontWeight: 700, fontSize: 13 }}>{t.name}</span>
                        <span className={`badge badge-${t.difficulty}`}>{t.label}</span>
                      </div>
                      <div style={{ fontSize: 11, color: "#64748b" }}>{t.id}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Task Info */}
            <div className="panel">
              <div className="panel-header">📋 &nbsp;Task Info</div>
              <div style={{ padding: "12px 14px" }}>
                <p style={{ fontSize: 12, color: "#94a3b8", lineHeight: 1.6, marginBottom: 10 }}>{task.description}</p>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {task.hints.map((h, i) => (
                    <div key={i} style={{ fontSize: 11, color: "#ffaa00", fontFamily: "'JetBrains Mono',monospace", background: "rgba(255,170,0,0.08)", border: "1px solid rgba(255,170,0,0.2)", borderRadius: 4, padding: "4px 8px" }}>
                      💡 {h}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Options */}
            <div className="panel">
              <div className="panel-header">⚙️ &nbsp;Options</div>
              <div style={{ padding: "12px 14px", display: "flex", flexDirection: "column", gap: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontSize: 12, color: "#94a3b8" }}>Manual Mode</div>
                    <div style={{ fontSize: 10, color: "#334155" }}>Type fix yourself</div>
                  </div>
                  <button onClick={() => setManualMode(m => !m)} style={{
                    width: 44, height: 24, borderRadius: 12, border: "none", cursor: "pointer",
                    background: manualMode ? "#00ff88" : "#1e293b", position: "relative", transition: "background 0.2s",
                  }}>
                    <span style={{ position: "absolute", top: 3, left: manualMode ? 22 : 3, width: 18, height: 18, background: "#fff", borderRadius: "50%", transition: "left 0.2s", display: "block" }} />
                  </button>
                </div>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontSize: 12, color: "#94a3b8" }}>Speed</span>
                    <span style={{ fontSize: 11, color: "#00ff88", fontFamily: "'JetBrains Mono',monospace" }}>{speed.toUpperCase()}</span>
                  </div>
                  <div style={{ display: "flex", gap: 6 }}>
                    {["slow", "normal", "fast"].map(s => (
                      <button key={s} className="btn btn-ghost" style={{ flex: 1, padding: "5px 0", fontSize: 10, borderColor: speed === s ? "#00ff88" : "#1e293b", color: speed === s ? "#00ff88" : "#64748b" }}
                        onClick={() => setSpeed(s)}>{s.charAt(0).toUpperCase() + s.slice(1)}</button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Episode Controls */}
            <div className="panel">
              <div className="panel-header">▶ &nbsp;Episode Controls</div>
              <div style={{ padding: "12px 14px", display: "flex", flexDirection: "column", gap: 8 }}>
                <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }}
                  disabled={isRunning} onClick={startEpisode}>
                  {isRunning ? <><span className="spinner" />Running...</> : "▶ Start Episode"}
                </button>
                <button className="btn btn-danger" style={{ width: "100%", justifyContent: "center" }}
                  onClick={() => { runningRef.current = false; resetEpisode(); }}>
                  ⏹ Reset
                </button>
              </div>
            </div>

            {/* Episode Stats */}
            {stepCount > 0 && (
              <div className="panel fade-in">
                <div className="panel-header">📊 &nbsp;Episode Stats</div>
                <div style={{ padding: "12px 14px", display: "flex", flexDirection: "column", gap: 8 }}>
                  <div className="stat-card">
                    <div style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.1em" }}>Step</div>
                    <div style={{ fontSize: 22, fontWeight: 700, color: "#e2e8f0", fontFamily: "'JetBrains Mono',monospace" }}>
                      {stepCount}<span style={{ fontSize: 12, color: "#64748b" }}> /5</span>
                    </div>
                  </div>
                  <div className="stat-card">
                    <div style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.1em" }}>Cumulative Reward</div>
                    <div style={{ fontSize: 22, fontWeight: 700, color: rewardColor(totalReward / (rewards.length || 1)), fontFamily: "'JetBrains Mono',monospace" }}>
                      {totalReward.toFixed(3)}
                    </div>
                  </div>
                  <div className="stat-card">
                    <div style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 4 }}>Status</div>
                    <span className="badge" style={{
                      background: uiMode === "done" && success ? "rgba(0,255,136,0.15)" : uiMode === "done" ? "rgba(255,68,85,0.15)" : "rgba(99,179,237,0.15)",
                      color: uiMode === "done" && success ? "#00ff88" : uiMode === "done" ? "#ff4455" : "#63b3ed",
                      border: `1px solid ${uiMode === "done" && success ? "rgba(0,255,136,0.3)" : uiMode === "done" ? "rgba(255,68,85,0.3)" : "rgba(99,179,237,0.3)"}`,
                    }}>
                      {{ idle: "IDLE", resetting: "RESETTING", agent_thinking: "THINKING", executing: "EXECUTING", done: success ? "✓ SUCCESS" : "✗ FAILED" }[uiMode]}
                    </span>
                  </div>
                  {tokenEst > 0 && (
                    <div style={{ fontSize: 10, color: "#334155", fontFamily: "'JetBrains Mono',monospace", textAlign: "right" }}>
                      ~{tokenEst} prompt tokens
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* ════════════════════ CENTER PANEL ════════════════════ */}
          <div style={{ padding: "16px 14px", borderRight: "1px solid #1e293b", overflowY: "auto", display: "flex", flexDirection: "column", gap: 14 }}>

            {/* Buggy Code */}
            <div className="panel">
              <div className="panel-header">
                <span style={{ color: "#ff4455" }}>⚠</span>&nbsp;Buggy Code
                <span style={{ marginLeft: "auto" }}><span className={`badge badge-${task.difficulty}`}>{task.id}</span></span>
              </div>
              <div style={{ padding: 14 }}>
                <pre className="code-block" style={{ color: "#f8c8c8", maxHeight: 170, overflowY: "auto" }}>
                  {/* Show real buggy code from env if available, else fallback to hardcoded */}
                  {(envState?.buggy_code) || task.buggy_code}
                </pre>
              </div>
            </div>

            {/* Agent's Fix */}
            <div
              className={`panel ${uiMode === "agent_thinking" ? "thinking-border" : ""} ${uiMode === "done" && success ? "success-glow" : ""}`}
              style={{ transition: "box-shadow 0.3s ease" }}
            >
              <div className="panel-header">
                <span style={{ color: "#a78bfa" }}>🦙</span>&nbsp;Agent's Fix
                {uiMode === "agent_thinking" && (
                  <span style={{ marginLeft: 8, display: "flex", alignItems: "center", gap: 6 }}>
                    <span className="spinner" />
                    <span className="blink" style={{ color: "#a78bfa", fontSize: 10 }}>OLLAMA THINKING...</span>
                  </span>
                )}
                <span style={{ marginLeft: "auto", fontSize: 10, color: "#334155", fontFamily: "'JetBrains Mono',monospace" }}>
                  {ollamaModel}
                </span>
              </div>
              <div style={{ padding: 14 }}>
                {manualMode && uiMode === "idle" ? (
                  <textarea rows={8} value={manualCode} onChange={e => setManualCode(e.target.value)}
                    placeholder={`# Enter your fix here...\n${task.buggy_code}`} style={{ minHeight: 160 }} />
                ) : (
                  <pre className="code-block" style={{ minHeight: 160, maxHeight: 240, overflowY: "auto" }}>
                    {streamingCode || agentCode || (
                      <span style={{ color: "#334155" }}>
                        {uiMode === "idle" ? "// Agent's fix will appear here..." : uiMode === "resetting" ? "// Calling /reset on OpenEnv..." : ""}
                      </span>
                    )}
                    {isTyping && <span className="blink" style={{ borderRight: "2px solid #a78bfa" }}>&nbsp;</span>}
                  </pre>
                )}
              </div>
            </div>

            {/* Execution Output (from real /step endpoint) */}
            <div className="panel">
              <div className="panel-header">
                💻&nbsp;Execution Output
                <span style={{ marginLeft: 6, fontSize: 9, color: "#334155", fontFamily: "'JetBrains Mono',monospace" }}>via OpenEnv /step</span>
                {uiMode === "executing" && (
                  <span style={{ marginLeft: 8, display: "flex", alignItems: "center", gap: 6 }}>
                    <span className="spinner" />
                    <span style={{ color: "#ffaa00", fontSize: 10 }}>RUNNING TESTS...</span>
                  </span>
                )}
              </div>
              <div style={{ padding: 14 }}>
                <div className="terminal-block" style={{ minHeight: 120, maxHeight: 200, overflowY: "auto" }}>
                  {execOutput.length === 0 ? (
                    <span style={{ color: "#334155" }}>$ python -m pytest  // awaiting /step...</span>
                  ) : (
                    execOutput.map((line, i) => (
                      <div key={i} style={{ color: termColor(line) }}><AnsiLine text={line} /></div>
                    ))
                  )}
                  {uiMode === "executing" && <span className="blink" style={{ color: "#00ff88" }}>█</span>}
                </div>
              </div>
            </div>

            {/* Done Card */}
            {uiMode === "done" && (
              <div className={`panel fade-in ${success ? "success-glow" : ""}`} style={{
                border: `1px solid ${success ? "#00ff88" : "#ff4455"}`,
                background: success ? "rgba(0,255,136,0.05)" : "rgba(255,68,85,0.05)",
              }}>
                <div style={{ padding: 20, textAlign: "center" }}>
                  <div style={{ fontSize: 36, marginBottom: 8 }}>{success ? "🏆" : "💀"}</div>
                  <div style={{ fontFamily: "'Rajdhani',sans-serif", fontWeight: 700, fontSize: 22, color: success ? "#00ff88" : "#ff4455", letterSpacing: "0.08em", marginBottom: 4 }}>
                    {success ? "EPISODE SUCCESS!" : "EPISODE FAILED"}
                  </div>
                  <div style={{ fontSize: 12, color: "#64748b", marginBottom: 16 }}>
                    Model: <span style={{ color: "#a78bfa", fontFamily: "'JetBrains Mono',monospace" }}>{ollamaModel}</span>
                    &nbsp;·&nbsp;Steps: {stepCount}
                    &nbsp;·&nbsp;Final Reward:&nbsp;
                    <span style={{ color: rewardColor(finalReward), fontFamily: "'JetBrains Mono',monospace" }}>{finalReward.toFixed(4)}</span>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                    {[
                      { label: "Steps", value: stepCount },
                      { label: "Avg Reward", value: (totalReward / (rewards.length || 1)).toFixed(3) },
                      { label: "Final Reward", value: finalReward.toFixed(3) },
                    ].map(s => (
                      <div className="stat-card" key={s.label} style={{ textAlign: "center" }}>
                        <div style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.1em" }}>{s.label}</div>
                        <div style={{ fontSize: 18, fontWeight: 700, color: success ? "#00ff88" : "#ff4455", fontFamily: "'JetBrains Mono',monospace" }}>{s.value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ════════════════════ RIGHT PANEL ════════════════════ */}
          <div style={{ padding: "16px 14px", overflowY: "auto", display: "flex", flexDirection: "column", gap: 14 }}>

            {/* Reward Chart */}
            <div className="panel">
              <div className="panel-header">
                📈 &nbsp;Reward Chart
                <span style={{ marginLeft: "auto", fontSize: 10, fontFamily: "'JetBrains Mono',monospace", color: "#334155" }}>Steps 1–5</span>
              </div>
              <div style={{ padding: "8px 14px 14px" }}>
                <RewardChart rewards={rewards} />
                {rewards.length === 0 && (
                  <div style={{ textAlign: "center", color: "#334155", fontSize: 11, fontFamily: "'JetBrains Mono',monospace", marginTop: 4 }}>
                    // No data yet
                  </div>
                )}
              </div>
            </div>

            {/* OpenEnv Live State */}
            {envState && (
              <div className="panel fade-in">
                <div className="panel-header">🔭 &nbsp;OpenEnv State</div>
                <div style={{ padding: "10px 14px", display: "flex", flexDirection: "column", gap: 8 }}>
                  <div style={{ fontSize: 11, fontFamily: "'JetBrains Mono',monospace" }}>
                    <span style={{ color: "#64748b" }}>test_results: </span>
                    <span style={{ color: "#00ff88" }}>{envState.test_results || "—"}</span>
                  </div>
                  <div style={{ fontSize: 11, fontFamily: "'JetBrains Mono',monospace" }}>
                    <span style={{ color: "#64748b" }}>error_log: </span>
                    <span style={{ color: "#ff8899" }}>{envState.error_log ? envState.error_log.slice(0, 80) + "..." : "—"}</span>
                  </div>
                  <div style={{ fontSize: 11, fontFamily: "'JetBrains Mono',monospace" }}>
                    <span style={{ color: "#64748b" }}>prev_attempts: </span>
                    <span style={{ color: "#ffaa00" }}>{(envState.previous_attempts || []).length}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Episode Log */}
            <div className="panel" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
              <div className="panel-header" style={{ justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  📜 &nbsp;Episode Log
                  {episodeLog.length > 0 && (
                    <span className="badge badge-info" style={{ fontSize: 9 }}>{episodeLog.length} step{episodeLog.length !== 1 ? "s" : ""}</span>
                  )}
                </div>
                {episodeLog.length > 0 && (
                  <button className="btn btn-ghost" style={{ padding: "3px 10px", fontSize: 10 }} onClick={copyJSON}>
                    {copied ? "✓ Copied!" : "⧉ Copy JSON"}
                  </button>
                )}
              </div>
              <div ref={logRef} style={{ flex: 1, overflowY: "auto", padding: "10px 12px", minHeight: 200, maxHeight: 420 }}>
                {episodeLog.length === 0 ? (
                  <div style={{ textAlign: "center", color: "#334155", fontSize: 11, fontFamily: "'JetBrains Mono',monospace", padding: "30px 0" }}>
                    // Episode log will appear here
                  </div>
                ) : (
                  episodeLog.map((entry, idx) => {
                    const isCollapsed = collapsedEntries.has(idx);
                    return (
                      <div key={idx} className="log-entry">
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
                          onClick={() => setCollapsedEntries(s => { const ns = new Set(s); ns.has(idx) ? ns.delete(idx) : ns.add(idx); return ns; })}>
                          <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: "#64748b" }}>STEP {entry.step}</span>
                          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 12, fontWeight: 700, color: rewardColor(entry.reward) }}>
                              R={entry.reward.toFixed(3)}
                            </span>
                            <span style={{ color: "#334155", fontSize: 10 }}>{isCollapsed ? "▶" : "▼"}</span>
                          </span>
                        </div>
                        <div className="reward-bar-outer">
                          <div className="reward-bar-inner" style={{
                            width: `${entry.reward * 100}%`,
                            background: `linear-gradient(90deg, ${rewardColor(0)}, ${rewardColor(entry.reward)})`,
                          }} />
                        </div>
                        <div style={{ fontSize: 10, color: "#64748b", fontFamily: "'JetBrains Mono',monospace", marginTop: 6 }}>
                          {entry.passed}/{entry.total} tests ·{" "}
                          {entry.done ? (entry.reward >= 0.99 ? "✅ SUCCESS" : "❌ DONE") : "⏳ continuing"}
                        </div>
                        {!isCollapsed && (
                          <>
                            {entry.test_results && (
                              <div style={{ fontSize: 10, color: "#a78bfa", fontFamily: "'JetBrains Mono',monospace", marginTop: 4 }}>
                                {entry.test_results}
                              </div>
                            )}
                            {entry.code_submitted && (
                              <pre className="code-block" style={{
                                marginTop: 8, fontSize: 10, maxHeight: 100, overflowY: "auto",
                                color: entry.reward >= 0.99 ? "#a8d8a8" : entry.reward >= 0.5 ? "#ffd580" : "#f8c8c8",
                              }}>{entry.code_submitted}</pre>
                            )}
                          </>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
