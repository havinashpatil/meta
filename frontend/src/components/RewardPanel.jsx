import { motion } from 'framer-motion';
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, ReferenceLine, Area, AreaChart
} from 'recharts';
import {
  Trophy, TrendingUp, Clock, Sparkles,
  CheckCircle2, XCircle, MessageSquareText, BarChart3
} from 'lucide-react';
import clsx from 'clsx';

function rewardColor(r) {
  if (r >= 0.75) return '#00FF88';
  if (r >= 0.45) return '#FFAA00';
  return '#FF4455';
}

function StatCard({ icon: Icon, label, value, color, subtitle }) {
  return (
    <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-xl p-3">
      <div className="flex items-center gap-2 mb-1.5">
        <Icon size={12} className={color || 'text-[var(--text-muted)]'} />
        <span className="text-[9px] font-bold tracking-[0.12em] uppercase text-[var(--text-muted)]">{label}</span>
      </div>
      <div className="text-xl font-bold font-mono" style={{ color: color ? undefined : 'var(--text-primary)' }}>
        <span className={color}>{value}</span>
      </div>
      {subtitle && <p className="text-[9px] text-[var(--text-muted)] mt-0.5">{subtitle}</p>}
    </div>
  );
}

function RewardChart({ rewards }) {
  const data = rewards.map((r, i) => ({ step: i + 1, reward: r }));
  // Pad to 5 steps for consistent chart
  for (let i = data.length + 1; i <= 5; i++) {
    data.push({ step: i, reward: null });
  }

  return (
    <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-xl p-3">
      <div className="flex items-center gap-2 mb-2">
        <BarChart3 size={12} className="text-emerald-400" />
        <span className="text-[9px] font-bold tracking-[0.12em] uppercase text-[var(--text-muted)]">
          Reward Curve
        </span>
      </div>
      <div className="h-[100px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="rewardGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00FF88" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#00FF88" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="step" stroke="#1E293B" tick={{ fill: '#334155', fontSize: 9, fontFamily: 'monospace' }} />
            <YAxis domain={[0, 1]} ticks={[0, 0.5, 1]} stroke="#1E293B" tick={{ fill: '#334155', fontSize: 9, fontFamily: 'monospace' }} />
            <ReferenceLine y={0.5} stroke="#1E293B" strokeDasharray="4 4" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0F172A', border: '1px solid #1E293B',
                borderRadius: 8, fontFamily: 'monospace', fontSize: 10,
              }}
              itemStyle={{ color: '#00FF88' }}
              formatter={(val) => val !== null ? val.toFixed(3) : '—'}
            />
            <Area type="monotone" dataKey="reward" stroke="#00FF88" strokeWidth={2}
              fill="url(#rewardGrad)" dot={{ fill: '#0B0F19', stroke: '#00FF88', strokeWidth: 2, r: 3 }}
              connectNulls={false} isAnimationActive />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function RewardPanel({
  rewards, stepCount, isDone,
  rewardComponents, feedback,
  attempts,
}) {
  const latestReward = rewards.length > 0 ? rewards[rewards.length - 1] : null;
  const avgReward = rewards.length > 0 ? rewards.reduce((a, b) => a + b, 0) / rewards.length : 0;
  const success = latestReward !== null && latestReward >= 0.85;

  return (
    <aside className="flex flex-col h-full border-l border-[var(--border-subtle)] bg-[var(--bg-secondary)] overflow-y-auto">

      {/* ── Reward Hero ───────────── */}
      <div className={clsx(
        'px-4 py-5 border-b border-[var(--border-subtle)] text-center',
        isDone && success && 'animate-pulse-glow'
      )}>
        <p className="text-[9px] font-bold tracking-[0.15em] uppercase text-[var(--text-muted)] mb-1">
          {isDone ? (success ? '✦ Episode Complete' : 'Episode Finished') : 'Current Reward'}
        </p>
        <motion.div
          key={latestReward}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 200 }}
          className="text-4xl font-bold font-mono"
          style={{ color: latestReward !== null ? rewardColor(latestReward) : 'var(--text-muted)' }}
        >
          {latestReward !== null ? latestReward.toFixed(3) : '—'}
        </motion.div>
        {isDone && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-2 flex items-center justify-center gap-1.5 text-xs font-medium"
          >
            {success
              ? <><CheckCircle2 size={14} className="text-emerald-400" /> <span className="text-emerald-400">All tests passed!</span></>
              : <><XCircle size={14} className="text-red-400" /> <span className="text-red-400">Incomplete fix</span></>}
          </motion.div>
        )}
      </div>

      {/* ── Stats Grid ────────────── */}
      <div className="px-3 py-3 grid grid-cols-2 gap-2">
        <StatCard icon={TrendingUp} label="Steps" value={`${stepCount}/5`} subtitle="Max 5 per episode" />
        <StatCard icon={Trophy} label="Average" value={avgReward.toFixed(3)}
          color={avgReward >= 0.7 ? 'text-emerald-400' : avgReward >= 0.4 ? 'text-amber-400' : 'text-red-400'}
          subtitle="Mean reward" />
      </div>

      {/* ── Chart ─────────────────── */}
      <div className="px-3 pb-3">
        <RewardChart rewards={rewards} />
      </div>

      {/* ── Reward Components ─────── */}
      {rewardComponents && (
        <div className="px-3 pb-3">
          <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-xl p-3">
            <div className="flex items-center gap-2 mb-2.5">
              <Sparkles size={12} className="text-purple-400" />
              <span className="text-[9px] font-bold tracking-[0.12em] uppercase text-[var(--text-muted)]">
                Reward Breakdown
              </span>
            </div>
            <div className="space-y-2">
              {[
                { label: 'Compile', value: rewardComponents.compile_score, color: '#63B3ED' },
                { label: 'Test Ratio', value: rewardComponents.test_ratio, color: '#00FF88' },
                { label: 'Efficiency', value: rewardComponents.efficiency, color: '#FFAA00' },
                { label: 'LLM Correct', value: rewardComponents.llm_correctness, color: '#A78BFA' },
                { label: 'LLM Security', value: rewardComponents.llm_security, color: '#F97316' },
                { label: 'LLM Quality', value: rewardComponents.llm_quality, color: '#EC4899' },
              ].map(({ label, value, color }) => (
                <div key={label}>
                  <div className="flex items-center justify-between text-[10px] mb-0.5">
                    <span className="text-[var(--text-muted)]">{label}</span>
                    <span className="font-mono font-medium" style={{ color }}>{(value ?? 0).toFixed(2)}</span>
                  </div>
                  <div className="h-1 bg-[var(--bg-primary)] rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${((value ?? 0) * 100)}%` }}
                      transition={{ duration: 0.6, ease: 'easeOut' }}
                      className="h-full rounded-full"
                      style={{ backgroundColor: color }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── LLM Feedback ──────────── */}
      {feedback && (
        <div className="px-3 pb-3">
          <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-xl p-3">
            <div className="flex items-center gap-2 mb-2">
              <MessageSquareText size={12} className="text-blue-400" />
              <span className="text-[9px] font-bold tracking-[0.12em] uppercase text-[var(--text-muted)]">
                Execution Info
              </span>
            </div>
            <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed font-mono whitespace-pre-wrap">
              {feedback}
            </p>
          </div>
        </div>
      )}

      {/* ── Attempt Timeline ──────── */}
      {attempts.length > 0 && (
        <div className="px-3 pb-4">
          <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-xl p-3">
            <div className="flex items-center gap-2 mb-2.5">
              <Clock size={12} className="text-amber-400" />
              <span className="text-[9px] font-bold tracking-[0.12em] uppercase text-[var(--text-muted)]">
                Attempt Timeline
              </span>
            </div>
            <div className="space-y-2">
              {attempts.map((a, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center gap-2"
                >
                  <div className="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold border"
                    style={{
                      borderColor: rewardColor(a.reward),
                      color: rewardColor(a.reward),
                      backgroundColor: `${rewardColor(a.reward)}15`,
                    }}
                  >
                    {i + 1}
                  </div>
                  <div className="flex-1 h-px bg-[var(--border-subtle)]" />
                  <span className="text-[10px] font-mono font-medium" style={{ color: rewardColor(a.reward) }}>
                    {a.reward.toFixed(3)}
                  </span>
                  <span className="text-[9px] text-[var(--text-muted)]">
                    {a.passed}/{a.total}
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
