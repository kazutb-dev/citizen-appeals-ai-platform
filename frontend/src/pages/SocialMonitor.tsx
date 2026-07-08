import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { motion } from 'framer-motion'
import { Eye, MessageCircle, Share2, ThumbsUp, TrendingDown, TrendingUp } from 'lucide-react'
import { useState } from 'react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  fetchDepartmentImpact,
  fetchReputation,
  fetchSentiment,
  fetchSocialPosts,
  fetchSourceActivity,
  fetchSpikes,
  fetchTopicTrends,
  fetchTrending,
} from '../api/social'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { CATEGORY_LABELS } from '../types/common'
import type { SocialPost } from '../types/social'

const PLATFORMS = [
  { key: 'telegram', label: 'Telegram', color: 'text-sky-400' },
  { key: 'tiktok', label: 'TikTok', color: 'text-pink-400' },
  { key: 'instagram', label: 'Instagram', color: 'text-fuchsia-400' },
  { key: 'youtube', label: 'YouTube', color: 'text-red-400' },
  { key: 'facebook', label: 'Facebook', color: 'text-blue-400' },
  { key: 'vk', label: 'VK', color: 'text-indigo-400' },
  { key: 'x', label: 'X', color: 'text-navy-200' },
]

const SENTIMENT_STYLES: Record<string, string> = {
  positive: 'border-risk-low/40 bg-risk-low/10 text-risk-low',
  neutral: 'border-slate-500/40 bg-slate-500/10 text-navy-300',
  negative: 'border-risk-medium/40 bg-risk-medium/10 text-risk-medium',
  alarming: 'border-risk-critical/40 bg-risk-critical/10 text-risk-critical',
}

const SENTIMENT_LABELS: Record<string, string> = {
  positive: 'Позитив',
  neutral: 'Нейтрально',
  negative: 'Негатив',
  alarming: 'Тревожно',
}

function fmt(n: number): string {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}к` : String(n)
}

function PostCard({ post, index }: { post: SocialPost; index: number }) {
  const platform = PLATFORMS.find((p) => p.key === post.platform)
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index * 0.04, 0.4) }}
      className="card p-4"
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs">
          <span className={`font-semibold ${platform?.color ?? 'text-navy-200'}`}>
            {platform?.label ?? post.platform}
          </span>
          <span className="text-navy-300">{post.source_name}</span>
          <span className="text-navy-500">{post.source_account}</span>
        </div>
        <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${SENTIMENT_STYLES[post.sentiment]}`}>
          {SENTIMENT_LABELS[post.sentiment] ?? post.sentiment}
        </span>
      </div>

      <p className="text-sm leading-relaxed text-navy-200">{post.post_text}</p>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-4 font-mono text-xs text-navy-400">
          <span className="flex items-center gap-1"><Eye className="h-3.5 w-3.5" /> {fmt(post.views)}</span>
          <span className="flex items-center gap-1"><ThumbsUp className="h-3.5 w-3.5" /> {fmt(post.likes)}</span>
          <span className="flex items-center gap-1"><MessageCircle className="h-3.5 w-3.5" /> {fmt(post.comments)}</span>
          <span className="flex items-center gap-1"><Share2 className="h-3.5 w-3.5" /> {fmt(post.shares)}</span>
        </div>
        <span className="text-[11px] text-navy-500">
          {format(new Date(post.post_date), 'dd MMM HH:mm', { locale: ru })}
          {post.region && ` · ${post.region}`}
          {post.category && ` · ${CATEGORY_LABELS[post.category] ?? post.category}`}
        </span>
      </div>

      {post.tags && post.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {post.tags.map((t) => (
            <span key={t} className="rounded bg-surface-card px-2 py-0.5 text-[10px] text-navy-300">
              #{t}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  )
}

function Feed() {
  const [platform, setPlatform] = useState('')
  const [riskLevel, setRiskLevel] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['social', { platform, riskLevel, page }],
    queryFn: () =>
      fetchSocialPosts({
        platform: platform || undefined,
        risk_level: riskLevel || undefined,
        page,
        page_size: 12,
      }),
  })
  const { data: trending, isLoading: trendingLoading } = useQuery({ queryKey: ['trending'], queryFn: fetchTrending })

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_300px]">
      <div className="space-y-4">
        <div className="card flex flex-wrap items-center gap-2 p-4">
          <button
            onClick={() => { setPlatform(''); setPage(1) }}
            className={`rounded-full px-3 py-1.5 text-xs transition ${!platform ? 'bg-teal-400/12 text-teal-400' : 'text-navy-300 hover:text-navy-100'}`}
          >
            Все
          </button>
          {PLATFORMS.map((p) => (
            <button
              key={p.key}
              onClick={() => { setPlatform(p.key); setPage(1) }}
              className={`rounded-full px-3 py-1.5 text-xs transition ${platform === p.key ? 'bg-teal-400/12 text-teal-400' : 'text-navy-300 hover:text-navy-100'}`}
            >
              {p.label}
            </button>
          ))}
          <select
            value={riskLevel}
            onChange={(e) => { setRiskLevel(e.target.value); setPage(1) }}
            className="input ml-auto !py-1.5 text-xs"
          >
            <option value="">Любой риск</option>
            <option value="critical">Критический</option>
            <option value="high">Высокий</option>
            <option value="medium">Средний</option>
            <option value="low">Низкий</option>
          </select>
        </div>

        {isLoading ? (
          <LoadingSpinner label="Загрузка ленты…" />
        ) : data?.items.length ? (
          <>
            <div className="space-y-3">
              {data.items.map((p, i) => (
                <PostCard key={p.id} post={p} index={i} />
              ))}
            </div>
            <div className="flex items-center justify-end gap-2 text-xs text-navy-400">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="btn-ghost !px-3 !py-1.5">←</button>
              <span className="font-mono">{page} / {totalPages}</span>
              <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="btn-ghost !px-3 !py-1.5">→</button>
            </div>
          </>
        ) : (
          <EmptyState title="Посты не найдены" hint="Добавьте источники в разделе Администрирование → Социальные источники" />
        )}
      </div>

      <div className="card h-fit p-4">
        <h2 className="mb-3 text-sm font-semibold text-navy-100">🔥 Топ упоминаний</h2>
        <div className="space-y-2">
          {trendingLoading ? (
            <LoadingSpinner />
          ) : trending && trending.length > 0 ? trending.map((t, i) => (
            <div key={t.topic} className="flex items-center gap-3 rounded-lg bg-surface px-3 py-2">
              <span className="font-mono text-xs text-navy-500">{i + 1}</span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium text-navy-200">{t.topic}</p>
                <p className="text-[10px] text-navy-400">
                  {t.post_count} постов · {fmt(t.total_views)} просмотров
                </p>
              </div>
              {(t.max_risk_level === 'high' || t.max_risk_level === 'critical') && (
                <span className="h-2 w-2 shrink-0 animate-pulseDot rounded-full bg-risk-critical" />
              )}
            </div>
          )) : <EmptyState title="Нет данных о трендах" />}
        </div>
      </div>
    </div>
  )
}

function Analytics() {
  const { data: sentiment } = useQuery({ queryKey: ['social-sentiment'], queryFn: () => fetchSentiment(30) })
  const { data: reputation } = useQuery({ queryKey: ['social-reputation'], queryFn: () => fetchReputation(30) })
  const { data: trends } = useQuery({ queryKey: ['social-topic-trends'], queryFn: fetchTopicTrends })
  const { data: spikes } = useQuery({ queryKey: ['social-spikes'], queryFn: fetchSpikes })
  const { data: sources } = useQuery({ queryKey: ['social-sources-activity'], queryFn: fetchSourceActivity })
  const { data: impact } = useQuery({ queryKey: ['social-dept-impact'], queryFn: fetchDepartmentImpact })

  const negativeTrends = trends?.filter((t) => t.dominant_sentiment === 'negative') ?? []
  const positiveTrends = trends?.filter((t) => t.dominant_sentiment === 'positive') ?? []
  const viral = [...(trends ?? [])].sort((a, b) => b.current_count - a.current_count).slice(0, 5)

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-2">
        <div className="card p-5">
          <h2 className="mb-4 text-sm font-semibold text-navy-100">Тональность упоминаний — 30 дней</h2>
          {sentiment ? (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={sentiment}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                <Tooltip contentStyle={{ background: '#0d1627', border: '1px solid #1e293b', fontSize: 12 }} />
                <Area type="monotone" dataKey="positive" name="Позитив" stackId="1" stroke="#22c55e" fill="#22c55e33" />
                <Area type="monotone" dataKey="neutral" name="Нейтрально" stackId="1" stroke="#64748b" fill="#64748b33" />
                <Area type="monotone" dataKey="negative" name="Негатив" stackId="1" stroke="#f59e0b" fill="#f59e0b33" />
                <Area type="monotone" dataKey="alarming" name="Тревожно" stackId="1" stroke="#ef4444" fill="#ef444433" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <LoadingSpinner />
          )}
        </div>

        <div className="card p-5">
          <h2 className="mb-4 text-sm font-semibold text-navy-100">Индекс репутации организации</h2>
          {reputation ? (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={reputation}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} />
                <YAxis domain={[-1, 1]} tick={{ fontSize: 10, fill: '#64748b' }} />
                <Tooltip contentStyle={{ background: '#0d1627', border: '1px solid #1e293b', fontSize: 12 }} />
                <Line type="monotone" dataKey="score" name="Индекс" stroke="#38bdf8" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <LoadingSpinner />
          )}
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <TrendList title="📉 Негативные тренды" items={negativeTrends} tone="negative" />
        <TrendList title="📈 Позитивные тренды" items={positiveTrends} tone="positive" />
        <div className="card p-5">
          <h2 className="mb-3 text-sm font-semibold text-navy-100">🔥 Вирусные темы</h2>
          <div className="space-y-2">
            {viral.length ? viral.map((t) => (
              <div key={t.topic} className="rounded-lg bg-surface px-3 py-2">
                <p className="text-xs font-medium text-navy-200">{t.topic}</p>
                <p className="text-[10px] text-navy-400">
                  {t.current_count} постов · рост {t.growth_pct > 0 ? '+' : ''}{t.growth_pct}%
                </p>
              </div>
            )) : <EmptyState title="Нет данных" />}
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="card p-5">
          <h2 className="mb-3 text-sm font-semibold text-navy-100">Активность источников — 30 дней</h2>
          {sources?.length ? (
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border text-left uppercase tracking-wider text-navy-400">
                  <th className="px-2 py-2">Источник</th>
                  <th className="px-2 py-2">Платформа</th>
                  <th className="px-2 py-2 text-right">Постов</th>
                  <th className="px-2 py-2 text-right">Просмотров</th>
                  <th className="px-2 py-2 text-right">Негатив</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((s) => (
                  <tr key={`${s.source_name}-${s.platform}`} className="border-b border-border/50">
                    <td className="px-2 py-2 text-navy-200">{s.source_name}</td>
                    <td className="px-2 py-2 text-navy-400">{s.platform}</td>
                    <td className="px-2 py-2 text-right font-mono text-navy-200">{s.post_count}</td>
                    <td className="px-2 py-2 text-right font-mono text-navy-300">{fmt(s.total_views)}</td>
                    <td className={`px-2 py-2 text-right font-mono ${s.negative_share > 0.5 ? 'text-risk-high' : 'text-navy-300'}`}>
                      {Math.round(s.negative_share * 100)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <EmptyState title="Нет данных по источникам" />
          )}
        </div>

        <div className="card p-5">
          <h2 className="mb-3 text-sm font-semibold text-navy-100">Влияние на подразделения</h2>
          {impact?.length ? (
            <div className="space-y-2">
              {impact.map((d) => (
                <div key={d.category} className="flex items-center gap-3 rounded-lg bg-surface px-3 py-2 text-xs">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-navy-200">
                      {CATEGORY_LABELS[d.category] ?? d.category}
                    </p>
                    <p className="text-[10px] text-navy-400">{d.department ?? 'Подразделение не определено'}</p>
                  </div>
                  <span className="font-mono text-navy-200">{d.post_count}</span>
                  {d.negative_count > 0 && (
                    <span className="font-mono text-risk-high">−{d.negative_count}</span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="Нет данных" />
          )}
          {spikes && spikes.length > 0 && (
            <div className="mt-4 border-t border-border pt-3">
              <p className="mb-2 text-xs font-semibold text-risk-high">⚡ Всплески активности</p>
              {spikes.map((s) => (
                <p key={s.date} className="text-[11px] text-navy-300">
                  {s.date}: {s.count} постов ({s.deviation}× от обычного)
                </p>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function TrendList({
  title,
  items,
  tone,
}: {
  title: string
  items: { topic: string; current_count: number; growth_pct: number }[]
  tone: 'negative' | 'positive'
}) {
  const Icon = tone === 'negative' ? TrendingDown : TrendingUp
  return (
    <div className="card p-5">
      <h2 className="mb-3 text-sm font-semibold text-navy-100">{title}</h2>
      <div className="space-y-2">
        {items.length ? items.slice(0, 5).map((t) => (
          <div key={t.topic} className="flex items-center gap-2 rounded-lg bg-surface px-3 py-2">
            <Icon className={`h-3.5 w-3.5 shrink-0 ${tone === 'negative' ? 'text-risk-high' : 'text-risk-low'}`} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium text-navy-200">{t.topic}</p>
              <p className="text-[10px] text-navy-400">
                {t.current_count} постов · {t.growth_pct > 0 ? '+' : ''}{t.growth_pct}%
              </p>
            </div>
          </div>
        )) : <EmptyState title="Нет данных" />}
      </div>
    </div>
  )
}

export function SocialMonitor() {
  const [tab, setTab] = useState<'feed' | 'analytics'>('feed')

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button
          onClick={() => setTab('feed')}
          className={`rounded-lg px-4 py-2 text-sm transition ${tab === 'feed' ? 'bg-teal-400/12 text-teal-400' : 'text-navy-300 hover:text-navy-100'}`}
        >
          Лента упоминаний
        </button>
        <button
          onClick={() => setTab('analytics')}
          className={`rounded-lg px-4 py-2 text-sm transition ${tab === 'analytics' ? 'bg-teal-400/12 text-teal-400' : 'text-navy-300 hover:text-navy-100'}`}
        >
          Аналитика
        </button>
      </div>
      {tab === 'feed' ? <Feed /> : <Analytics />}
    </div>
  )
}
