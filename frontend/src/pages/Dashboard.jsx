import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wifi, WifiOff, Sparkles, Loader2, X } from 'lucide-react';

import Sidebar from '../components/Sidebar';
import CodeEditor from '../components/CodeEditor';
import Terminal from '../components/Terminal';
import RewardPanel from '../components/RewardPanel';
import { resetTask, sendStep, healthCheck, generateFix, runRaw } from '../services/api';

function initialState() {
  return {
    code: '# Select a task and click "Start Episode" to begin.\n',
    selectedTask: 'easy',
    stepCount: 0,
    maxSteps: 5,
    rewards: [],
    isDone: false,
    isRunning: false,
    isThinking: false,
    isGenerating: false,
    terminalLogs: [],
    rewardComponents: null,
    feedback: '',
    attempts: [],
    episodeHistory: [],
    serverStatus: 'checking',
    errorBanner: '',
    currentTaskId: '',
    currentDifficulty: '',
    ollamaModel: 'llama3.2:latest',
    agentMode: false,
    lastFixMethod: '',
  };
}

export default function Dashboard() {
  const [state, setState] = useState(initialState);
  const stateRef = useRef(state);
  stateRef.current = state;

  const set = useCallback((patch) => {
    setState(prev => ({ ...prev, ...(typeof patch === 'function' ? patch(prev) : patch) }));
  }, []);

  // Health probe
  useEffect(() => {
    const probe = async () => {
      set({ serverStatus: 'checking' });
      try { await healthCheck(); set({ serverStatus: 'online' }); }
      catch { set({ serverStatus: 'offline' }); }
    };
    probe();
    const iv = setInterval(probe, 15000);
    return () => clearInterval(iv);
  }, [set]);

  const pushLog = useCallback((text, type = 'info') => {
    set(prev => ({ terminalLogs: [...prev.terminalLogs, { text, type }] }));
  }, [set]);

  const resetEpisode = useCallback(() => {
    set({
      code: '# Select a task and click "Start Episode" to begin.\n',
      stepCount: 0, rewards: [], isDone: false, isRunning: false,
      isThinking: false, isGenerating: false, terminalLogs: [],
      rewardComponents: null, feedback: '', attempts: [],
      errorBanner: '', currentTaskId: '', currentDifficulty: '', lastFixMethod: '',
    });
  }, [set]);

  // START EPISODE
  const handleStartEpisode = useCallback(async () => {
    const s = stateRef.current;
    if (s.isRunning || s.serverStatus !== 'online') return;
    resetEpisode();
    await new Promise(r => setTimeout(r, 50));
    set({ isRunning: true, errorBanner: '' });

    const logs = [
      { text: `$ codearena reset --task=${s.selectedTask}`, type: 'command' },
      { text: 'Connecting to environment…', type: 'info' },
    ];
    set({ terminalLogs: logs });

    if (s.selectedTask === 'sandbox') {
      logs.push({ text: `✓ Sandbox loaded. Max 5 episodes. Write custom code and click RUN STEP!`, type: 'success' });
      logs.push({ text: `📋 The AI will run all 5 steps automatically after each execution.`, type: 'info' });
      set({
        code: '# Write custom python code here...\n\n',
        terminalLogs: [...logs],
        isRunning: false,
        stepCount: 0,
        isDone: false,
        rewards: [],
        attempts: [],
        currentTaskId: 'sandbox',
        currentDifficulty: 'sandbox',
      });
      return;
    }

    try {
      const data = await resetTask(s.selectedTask);
      const obs = data.observation || {};
      const info = data.info || {};
      logs.push({ text: `✓ Task loaded: ${info.task_id} [${info.difficulty}]`, type: 'success' });
      logs.push({ text: 'Edit the code and click RUN STEP, or use AI FIX.', type: 'info' });
      set({
        code: obs.buggy_code || '# No code returned',
        terminalLogs: [...logs],
        isRunning: false,
        currentTaskId: info.task_id || s.selectedTask,
        currentDifficulty: info.difficulty || '',
      });
    } catch (err) {
      logs.push({ text: `✗ Reset failed: ${err.message}`, type: 'error' });
      set({ terminalLogs: [...logs], isRunning: false, errorBanner: `Reset failed: ${err.message}` });
    }
  }, [set, resetEpisode]);

  // AI FIX — calls backend /fix (built-in fixer + optional Ollama)
  const handleAIFix = useCallback(async () => {
    const s = stateRef.current;
    if (s.isGenerating || s.isDone) return;

    set({ isGenerating: true, errorBanner: '' });
    pushLog(`$ codearena fix --model=${s.ollamaModel}`, 'command');
    pushLog('Generating fix (Ollama → built-in fallback)…', 'info');

    try {
      const result = await generateFix(
        s.code,
        s.feedback,
        'http://localhost:11434',
        s.ollamaModel,
        s.rewards.length > 0 ? s.rewards[s.rewards.length - 1] : 0.0,
        s.currentTaskId || 'sandbox'
      );
      const method = result.method === 'ollama' ? '🤖 Ollama' : '⚙️  Built-in';
      pushLog(`✓ Fix generated via ${method}`, 'success');

      if (result.algo_hint) {
        pushLog(`🔍 Algorithm: ${result.algo_hint}`, 'warning');
      }
      if (result.complexity) {
        pushLog(`⏱ Complexity of fix: ${result.complexity}`, 'info');
      }
      
      if (result.explanation && result.explanation !== "No reasoning provided.") {
        pushLog('', 'info');
        pushLog('🧠 AI Analysis:', 'warning');
        result.explanation.split('\n').filter(Boolean).forEach(l => pushLog(`  ${l}`, 'info'));
        pushLog('', 'info');
      }

      if (result.note) pushLog(result.note, 'info');
      const codeChanged = result.fixed_code.trim() !== s.code.trim();
      
      set({ code: result.fixed_code, isGenerating: false, lastFixMethod: result.method });

      // If agent mode, auto-run step (only if code actually changed to prevent infinite loops)
      if (s.agentMode && codeChanged) {
        setTimeout(handleRunStep, 1500);
      } else if (s.agentMode && !codeChanged) {
        pushLog(`✓ AI determined code is already optimal. Agent Mode stopping.`, 'success');
      }
    } catch (err) {
      pushLog(`✗ Fix failed: ${err.message}`, 'error');
      set({ isGenerating: false, errorBanner: `Fix failed: ${err.message}` });
    }
  }, [set, pushLog]);

  // RUN RAW (Sandbox mode)
  const handleRunRaw = useCallback(async () => {
    const s = stateRef.current;
    if (s.isRunning || !s.code?.trim()) return;

    // Enforce max 5 episodes for Sandbox
    if (s.stepCount >= 5) {
      pushLog('', 'info');
      pushLog('🏁 Max 5 episodes reached! Click "Start Episode" to reset and try again.', 'warning');
      set({ isDone: true });
      return;
    }

    const episodeNum = s.stepCount + 1;
    set({ isRunning: true, isThinking: true, errorBanner: '' });
    const logs = [...stateRef.current.terminalLogs,
      { text: '', type: 'info' },
      { text: `$ sandbox_runner.py  [Episode ${episodeNum}/5]`, type: 'command' },
      { text: `⏳ Step 1/5: Executing custom code… (Episode ${episodeNum} of 5)`, type: 'info' },
    ];
    set({ terminalLogs: logs });

    try {
      const data = await runRaw(s.code);
      set({ isThinking: false });

      logs.push({ text: '─'.repeat(40), type: 'info' });
      logs.push({ text: '✅ Step 1: Execution complete', type: 'success' });

      if (data.stdout) data.stdout.split('\n').filter(Boolean).forEach(l => logs.push({ text: `  ${l}`, type: 'success' }));

      if (data.stderr) {
        logs.push({ text: '⚠️  Step 2: Errors detected:', type: 'warning' });
        data.stderr.split('\n').filter(Boolean).forEach(l => logs.push({ text: `  ${l}`, type: 'error' }));
      } else {
        logs.push({ text: '✅ Step 2: No runtime errors found', type: 'success' });
      }

      logs.push({ text: '', type: 'info' });
      logs.push({ text: `✅ Step 3: ⏱ Execution Time: ${data.execution_time?.toFixed(4) ?? 'N/A'}s`, type: 'info' });
      logs.push({ text: `✅ Step 4: 🧠 Complexity: ${data.time_complexity_hint}`, type: 'warning' });
      logs.push({ text: `⏳ Step 5: 🤖 Running AI Optimization Analysis…`, type: 'info' });
      logs.push({ text: '', type: 'info' });

      const isLastEpisode = episodeNum >= 5;
      const avgReward = stateRef.current.rewards.length > 0
        ? (([...stateRef.current.rewards, data.reward ?? 0.5].reduce((a,b)=>a+b,0)) / (stateRef.current.rewards.length + 1)).toFixed(3)
        : (data.reward ?? 0.5).toFixed(3);

      set(prev => ({
        terminalLogs: [...logs],
        stepCount: prev.stepCount + 1,
        rewards: [...prev.rewards, data.reward ?? 0.5],
        isDone: isLastEpisode,
        isRunning: false,
        rewardComponents: data.reward_components || prev.rewardComponents,
        feedback: data.time_complexity_hint || '',
        attempts: [...prev.attempts, { reward: data.reward ?? 0.5, passed: data.stderr ? 0 : 1, total: 1 }],
      }));

      if (isLastEpisode) {
        pushLog('', 'info');
        pushLog(`🏁 Episode 5/5 complete! Avg Reward: ${avgReward}`, 'success');
        pushLog(`📊 Click "Start Episode" to start a new run.`, 'info');
        return; // Don't trigger AI fix on last episode done
      }

      // Step 5: ALWAYS auto-trigger AI 5-step analysis for Custom Code (same as all other tasks)
      setTimeout(handleAIFix, 800);
    } catch (err) {
      const logs2 = [...stateRef.current.terminalLogs, { text: `✗ Execution failed: ${err.message}`, type: 'error' }];
      set({ terminalLogs: logs2, isRunning: false, isThinking: false, errorBanner: `Run failed: ${err.message}` });
    }
  }, [set]);

  // RUN STEP
  const handleRunStep = useCallback(async () => {
    const s = stateRef.current;
    if (s.selectedTask === 'sandbox') {
      return handleRunRaw();
    }
    if (s.isRunning || s.isDone || !s.code?.trim()) return;

    set({ isRunning: true, isThinking: true, errorBanner: '' });
    const stepNum = s.stepCount + 1;
    const logs = [...stateRef.current.terminalLogs,
      { text: '', type: 'info' },
      { text: `$ codearena step --step=${stepNum}`, type: 'command' },
      { text: 'Submitting fix…', type: 'info' },
    ];
    set({ terminalLogs: logs });

    try {
      const data = await sendStep(s.code);
      set({ isThinking: false });

      const { observation, reward, done, info } = data;
      const meta = info?.execution_metadata || {};
      const rc = info?.reward_components || {};
      const passed = meta.test_passed ?? 0;
      const total = meta.test_total ?? 0;
      const errors = meta.runtime_errors || '';

      logs.push({ text: '─'.repeat(40), type: 'info' });
      if (passed === total && total > 0) {
        logs.push({ text: `✓ All ${total} tests passed`, type: 'success' });
      } else {
        logs.push({ text: `✗ ${passed}/${total} tests passed`, type: 'error' });
        if (errors) errors.split('\n').slice(0, 4).forEach(l => logs.push({ text: l, type: 'error' }));
      }
      logs.push({ text: `Reward: ${reward.toFixed(4)} | Done: ${done}`, type: reward >= 0.7 ? 'success' : 'warning' });

      if (done) {
        logs.push({ text: '', type: 'info' });
        logs.push({
          text: reward >= 0.85 ? '🎉 Episode complete — fix accepted!' : '⚠ Episode ended.',
          type: reward >= 0.85 ? 'success' : 'warning'
        });
      }

      const feedbackText = (observation?.error_log || '') || (observation?.test_results || '');

      set(prev => ({
        terminalLogs: [...logs],
        stepCount: stepNum,
        rewards: [...prev.rewards, reward],
        isDone: done,
        isRunning: false,
        rewardComponents: Object.keys(rc).length > 0 ? rc : prev.rewardComponents,
        feedback: feedbackText || prev.feedback,
        attempts: [...prev.attempts, { reward, passed, total }],
        episodeHistory: done
          ? [{ taskId: prev.currentTaskId, reward, steps: stepNum, ts: new Date().toISOString() }, ...prev.episodeHistory].slice(0, 20)
          : prev.episodeHistory,
      }));

      // Agent mode: if not done, auto-fix and retry
      if (s.agentMode && !done) {
        setTimeout(handleAIFix, 1000);
      }
    } catch (err) {
      const logs2 = [...stateRef.current.terminalLogs, { text: `✗ Step failed: ${err.message}`, type: 'error' }];
      set({ terminalLogs: logs2, isRunning: false, isThinking: false, errorBanner: `Step failed: ${err.message}` });
    }
  }, [set, handleAIFix]);

  const isBusy = state.isRunning || state.isGenerating;

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[var(--bg-primary)]">
      {/* Navbar */}
      <nav className="h-11 flex items-center justify-between px-4 border-b border-[var(--border-subtle)] bg-[#070B14]">
        <span className="text-xs font-bold tracking-wider">
          Code<span className="text-emerald-400">Arena</span>
          <span className="text-purple-400 ml-0.5">RL</span>
        </span>
        <div className="flex items-center gap-4">
          {state.lastFixMethod && (
            <span className="text-[9px] font-mono text-purple-400 border border-purple-500/30 px-2 py-0.5 rounded">
              {state.lastFixMethod === 'ollama' ? '🤖 Ollama Fix' : '⚙️ Built-in Fix'}
            </span>
          )}
          <div className="flex items-center gap-1.5 text-[10px] font-mono text-[var(--text-muted)]">
            {state.serverStatus === 'online'
              ? <><Wifi size={11} className="text-emerald-400" /> FastAPI Online</>
              : <><WifiOff size={11} className="text-red-400" /> Offline</>
            }
          </div>
        </div>
      </nav>

      {/* Error Banner */}
      <AnimatePresence>
        {state.errorBanner && (
          <motion.div
            initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
            className="bg-red-500/10 border-b border-red-500/30 px-4 py-2 flex items-center justify-between"
          >
            <span className="text-[11px] font-mono text-red-300">{state.errorBanner}</span>
            <button onClick={() => set({ errorBanner: '' })}><X size={14} className="text-red-400" /></button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 3-Panel Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT — Sidebar */}
        <div className="w-[260px] min-w-[260px] flex flex-col">
          <Sidebar
            selectedTask={state.selectedTask}
            onSelectTask={(id) => { resetEpisode(); set({ selectedTask: id }); }}
            onStartEpisode={handleStartEpisode}
            onReset={resetEpisode}
            isRunning={isBusy}
            episodeHistory={state.episodeHistory}
            serverStatus={state.serverStatus}
          />
          {/* Agent Mode Controls */}
          <div className="p-3 border-t border-[var(--border-subtle)] bg-[var(--bg-secondary)] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-1">
                <Sparkles size={10} className="text-purple-400" /> Agent Mode
              </span>
              <button
                onClick={() => set({ agentMode: !state.agentMode })}
                className={`w-8 h-4 rounded-full transition-colors relative ${state.agentMode ? 'bg-emerald-500' : 'bg-slate-700'}`}
              >
                <div className={`absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full transition-transform ${state.agentMode ? 'translate-x-4' : ''}`} />
              </button>
            </div>
            <div className="space-y-1">
              <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Ollama Model</span>
              <input
                className="w-full bg-[#0D1117] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] text-emerald-400 font-mono focus:border-emerald-500 outline-none"
                value={state.ollamaModel}
                onChange={(e) => set({ ollamaModel: e.target.value })}
                placeholder="llama3.2:latest"
              />
              <p className="text-[9px] text-[var(--text-muted)]">Falls back to built-in if unavailable</p>
            </div>
          </div>
        </div>

        {/* CENTER — Editor + Terminal */}
        <div className="flex-1 flex flex-col min-w-0 p-2 gap-2">
          <div className="flex-[3] min-h-0 relative">
            <CodeEditor
              code={state.code}
              onCodeChange={(val) => set({ code: val })}
              onRunStep={handleRunStep}
              isRunning={state.isRunning}
              isThinking={state.isThinking}
              stepCount={state.stepCount}
              isDone={state.isDone}
            />
            {/* AI Fix Button */}
            {!state.isDone && !isBusy && (
              <motion.button
                whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={handleAIFix}
                className="absolute top-12 right-6 flex items-center gap-2 bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/50 text-purple-300 px-3 py-1.5 rounded-lg text-[10px] font-bold backdrop-blur-sm transition-all z-10"
              >
                <Sparkles size={12} /> AI FIX
              </motion.button>
            )}
            {/* Generating Overlay */}
            <AnimatePresence>
              {state.isGenerating && (
                <motion.div
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className="absolute inset-0 bg-[#0B0F19]/70 backdrop-blur-[2px] flex items-center justify-center z-50"
                >
                  <div className="flex flex-col items-center gap-3 bg-[var(--bg-elevated)] border border-purple-500/30 rounded-xl p-6">
                    <Loader2 size={28} className="text-purple-400 animate-spin" />
                    <span className="text-xs font-mono text-purple-300">Generating fix…</span>
                    <span className="text-[10px] text-[var(--text-muted)]">Trying Ollama → built-in fallback</span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <div className="flex-[2] min-h-0">
            <Terminal logs={state.terminalLogs} isRunning={isBusy} />
          </div>
        </div>

        {/* RIGHT — Reward Panel */}
        <div className="w-[300px] min-w-[300px]">
          <RewardPanel
            rewards={state.rewards}
            stepCount={state.stepCount}
            isDone={state.isDone}
            rewardComponents={state.rewardComponents}
            feedback={state.feedback}
            attempts={state.attempts}
          />
        </div>
      </div>
    </div>
  );
}
