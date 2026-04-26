import { useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { motion } from 'framer-motion';
import { Code2, Loader2, Send } from 'lucide-react';
import clsx from 'clsx';

export default function CodeEditor({
  code, onCodeChange,
  onRunStep, isRunning, isThinking,
  stepCount, isDone,
}) {
  const editorRef = useRef(null);

  function handleMount(editor) {
    editorRef.current = editor;
    editor.updateOptions({
      fontSize: 13,
      lineHeight: 22,
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      renderLineHighlight: 'gutter',
      padding: { top: 12, bottom: 12 },
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      fontLigatures: true,
      cursorBlinking: 'smooth',
      smoothScrolling: true,
      bracketPairColorization: { enabled: true },
    });
  }

  // Auto-resize height based on content
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.layout();
    }
  }, [code]);

  return (
    <div className="glass-card flex flex-col overflow-hidden h-full">
      {/* ── Header ─────────────── */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--border-subtle)] bg-[#0D1117]/60">
        <div className="flex items-center gap-2">
          <Code2 size={14} className="text-emerald-400" />
          <span className="text-[10px] font-bold tracking-[0.12em] uppercase text-[var(--text-muted)]">
            Code Editor
          </span>
          {stepCount > 0 && (
            <span className="text-[9px] font-mono text-[var(--text-muted)] bg-[var(--bg-elevated)] px-2 py-0.5 rounded">
              Step {stepCount}/5
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {isThinking && (
            <motion.div
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-1.5 text-[10px] text-amber-400 font-mono"
            >
              <Loader2 size={12} className="animate-spin" />
              Thinking…
            </motion.div>
          )}

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            disabled={isRunning || isDone || !code?.trim()}
            onClick={onRunStep}
            className={clsx(
              'flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-[11px] font-bold tracking-wide',
              'transition-all duration-200 cursor-pointer',
              'disabled:opacity-30 disabled:cursor-not-allowed',
              isDone
                ? 'bg-[var(--bg-elevated)] text-[var(--text-muted)]'
                : 'bg-gradient-to-r from-emerald-500 to-emerald-600 text-black hover:shadow-[0_0_16px_rgba(0,255,136,0.3)]'
            )}
          >
            {isRunning ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
            {isDone ? 'DONE' : 'RUN STEP'}
          </motion.button>
        </div>
      </div>

      {/* ── Monaco Editor ──────── */}
      <div className="flex-1 min-h-0">
        <Editor
          height="100%"
          language="python"
          theme="vs-dark"
          value={code}
          onChange={(val) => onCodeChange(val || '')}
          onMount={handleMount}
          loading={
            <div className="flex items-center justify-center h-full gap-2 text-[var(--text-muted)] text-xs">
              <Loader2 size={14} className="animate-spin" /> Loading editor…
            </div>
          }
          options={{
            readOnly: isRunning,
          }}
        />
      </div>
    </div>
  );
}
