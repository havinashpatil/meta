import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal as TerminalIcon, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

function parseLineColor(line) {
  if (line.includes('PASS') || line.includes('OK') || line.includes('passed'))
    return 'text-emerald-400';
  if (line.includes('FAIL') || line.includes('Error') || line.includes('error') || line.includes('✗'))
    return 'text-red-400';
  if (line.includes('---') || line.includes('Ran ') || line.includes('==='))
    return 'text-[var(--text-muted)]';
  if (line.startsWith('>') || line.startsWith('$'))
    return 'text-emerald-300';
  return 'text-[var(--text-secondary)]';
}

export default function Terminal({ logs, isRunning }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const hasErrors = logs.some(l => l.type === 'error');
  const hasSuccess = logs.some(l => l.type === 'success');

  return (
    <div className="glass-card flex flex-col overflow-hidden h-full">
      {/* ── Header ─────────────── */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--border-subtle)] bg-[#0D1117]/60">
        <div className="flex items-center gap-2">
          <TerminalIcon size={14} className="text-emerald-400" />
          <span className="text-[10px] font-bold tracking-[0.12em] uppercase text-[var(--text-muted)]">
            Terminal Output
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {hasSuccess && <CheckCircle2 size={14} className="text-emerald-400" />}
          {hasErrors && <XCircle size={14} className="text-red-400" />}
          {isRunning && (
            <span className="flex items-center gap-1 text-[10px] text-amber-400 font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              running
            </span>
          )}
        </div>
      </div>

      {/* ── Log Output ─────────── */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 font-mono text-xs leading-[1.8]">
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-[var(--text-muted)]">
            <AlertCircle size={20} />
            <p className="text-[11px]">Waiting for execution…</p>
            <p className="text-[9px]">Click "Run Step" to submit code</p>
          </div>
        ) : (
          <AnimatePresence>
            {logs.map((log, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.15, delay: i * 0.02 }}
                className={`${parseLineColor(log.text)} whitespace-pre-wrap`}
              >
                {log.prefix && (
                  <span className="text-[var(--text-muted)] select-none mr-2">{log.prefix}</span>
                )}
                {log.text}
              </motion.div>
            ))}
          </AnimatePresence>
        )}

        {isRunning && (
          <span className="terminal-cursor text-emerald-400 text-xs"> </span>
        )}
      </div>
    </div>
  );
}
