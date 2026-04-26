import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play, RotateCcw, Zap, Shield, AlertTriangle,
  ChevronRight, Cpu, Gauge
} from 'lucide-react';
import clsx from 'clsx';

const TASKS = [
  {
    id: 'auto', label: 'Auto', name: 'Adaptive Curriculum', difficulty: 'info', icon: Gauge,
    desc: 'Scales difficulty based on agent performance.'
  },
  {
    id: 'easy', label: 'Easy', name: 'Fix average_list()', difficulty: 'easy', icon: Zap,
    desc: 'Syntax errors — missing colon, wrong built-in.'
  },
  {
    id: 'medium', label: 'Medium', name: 'Fix binary_search()', difficulty: 'medium', icon: Cpu,
    desc: 'Logic bugs — off-by-one, infinite loop.'
  },
  {
    id: 'hard', label: 'Hard', name: 'Optimize subarray', difficulty: 'hard', icon: AlertTriangle,
    desc: 'Replace O(N³) with Kadane\'s O(N).'
  },
  {
    id: 'sandbox', label: 'Sandbox', name: 'Custom Code & Debug', difficulty: 'sandbox', icon: Play,
    desc: 'Write custom code, debug it, and measure time complexity.'
  },
];

const diffColors = {
  info: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400', dot: 'bg-blue-400' },
  easy: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400', dot: 'bg-emerald-400' },
  medium: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400', dot: 'bg-amber-400' },
  hard: { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', dot: 'bg-red-400' },
  sandbox: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400', dot: 'bg-purple-400' },
};

export default function Sidebar({
  selectedTask, onSelectTask,
  onStartEpisode, onReset,
  isRunning, episodeHistory,
  serverStatus,
}) {
  const [historyOpen, setHistoryOpen] = useState(false);

  return (
    <aside className="flex flex-col h-full border-r border-[var(--border-subtle)] bg-[var(--bg-secondary)] overflow-hidden">

      {/* ── Header ─────────────────────── */}
      <div className="px-4 py-4 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
            <span className="text-sm font-bold text-black">C</span>
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wide text-[var(--text-primary)]">
              Code<span className="text-emerald-400">Arena</span>
              <span className="text-purple-400 ml-1">RL</span>
            </h1>
            <p className="text-[10px] text-[var(--text-muted)] tracking-widest uppercase">
              Debug Benchmark
            </p>
          </div>
        </div>

        {/* Server status */}
        <div className="mt-3 flex items-center gap-2 text-[11px]">
          <span className={clsx(
            'w-2 h-2 rounded-full',
            serverStatus === 'online' ? 'bg-emerald-400 shadow-[0_0_6px_rgba(0,255,136,0.5)]' :
              serverStatus === 'checking' ? 'bg-amber-400 animate-pulse' : 'bg-red-400'
          )} />
          <span className="text-[var(--text-muted)] font-mono">
            FastAPI {serverStatus === 'online' ? '● Online' : serverStatus === 'checking' ? '○ Checking…' : '✗ Offline'}
          </span>
        </div>
      </div>

      {/* ── Task Selector ──────────────── */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        <p className="text-[10px] font-semibold tracking-[0.15em] uppercase text-[var(--text-muted)] px-1 mb-1">
          Select Task
        </p>

        {TASKS.map((t) => {
          const colors = diffColors[t.difficulty];
          const active = selectedTask === t.id;
          const Icon = t.icon;

          return (
            <motion.button
              key={t.id}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              disabled={isRunning}
              onClick={() => onSelectTask(t.id)}
              className={clsx(
                'w-full text-left rounded-xl p-3 transition-all duration-200 border cursor-pointer',
                'disabled:opacity-40 disabled:cursor-not-allowed',
                active
                  ? `${colors.bg} ${colors.border} shadow-lg`
                  : 'bg-[var(--bg-elevated)] border-[var(--border-subtle)] hover:border-[var(--border-active)]'
              )}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <Icon size={14} className={active ? colors.text : 'text-[var(--text-muted)]'} />
                  <span className={clsx('text-xs font-semibold', active ? colors.text : 'text-[var(--text-primary)]')}>
                    {t.name}
                  </span>
                </div>
                <span className={clsx(
                  'text-[9px] font-bold tracking-wider uppercase px-2 py-0.5 rounded',
                  colors.bg, colors.text, 'border', colors.border
                )}>
                  {t.label}
                </span>
              </div>
              <p className="text-[10px] text-[var(--text-muted)] leading-relaxed pl-[22px]">{t.desc}</p>
            </motion.button>
          );
        })}
      </div>

      {/* ── Actions ────────────────────── */}
      <div className="px-3 pb-3 space-y-2">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          disabled={isRunning || serverStatus !== 'online'}
          onClick={onStartEpisode}
          className={clsx(
            'w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-bold tracking-wide',
            'transition-all duration-200 cursor-pointer',
            'disabled:opacity-40 disabled:cursor-not-allowed',
            'bg-gradient-to-r from-emerald-500 to-emerald-600 text-black',
            'hover:shadow-[0_0_20px_rgba(0,255,136,0.3)]'
          )}
        >
          <Play size={14} /> START EPISODE
        </motion.button>

        <button
          disabled={isRunning}
          onClick={onReset}
          className={clsx(
            'w-full flex items-center justify-center gap-2 py-2 rounded-xl text-xs font-medium',
            'border border-[var(--border-subtle)] text-[var(--text-secondary)]',
            'hover:border-[var(--border-active)] hover:text-[var(--text-primary)]',
            'transition-all disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer'
          )}
        >
          <RotateCcw size={12} /> Reset
        </button>
      </div>

      {/* ── Episode History ────────────── */}
      <div className="border-t border-[var(--border-subtle)]">
        <button
          onClick={() => setHistoryOpen(o => !o)}
          className="w-full flex items-center justify-between px-4 py-2.5 text-[10px] font-semibold tracking-[0.15em] uppercase text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors cursor-pointer"
        >
          <span>History ({episodeHistory.length})</span>
          <ChevronRight size={12} className={clsx('transition-transform', historyOpen && 'rotate-90')} />
        </button>

        <AnimatePresence>
          {historyOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="px-3 pb-3 space-y-1.5 max-h-40 overflow-y-auto">
                {episodeHistory.length === 0 && (
                  <p className="text-[10px] text-[var(--text-muted)] italic px-1">No episodes yet</p>
                )}
                {episodeHistory.map((ep, i) => (
                  <div key={i} className="flex items-center justify-between bg-[var(--bg-elevated)] rounded-lg px-3 py-2 text-[10px]">
                    <span className="text-[var(--text-secondary)] font-mono">
                      #{episodeHistory.length - i} · {ep.taskId}
                    </span>
                    <span className="font-bold font-mono" style={{ color: ep.reward >= 0.7 ? '#00FF88' : ep.reward >= 0.4 ? '#FFAA00' : '#FF4455' }}>
                      {ep.reward.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </aside>
  );
}
