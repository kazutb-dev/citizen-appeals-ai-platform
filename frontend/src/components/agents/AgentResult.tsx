import { motion } from 'framer-motion'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { REQUESTER_CATEGORY_LABELS, RISK_LABELS } from '../../types/common'
import type { RiskLevel } from '../../types/common'
import { AGENT_BY_KEY } from './agentMeta'

function ScoreBar({ value, label, tone = 'primary' }: { value: number; label: string; tone?: 'primary' | 'danger' }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-navy-300">{label}</span>
        <span className="font-mono text-navy-200">{Math.round(value * 100)}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-border">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, value * 100)}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className={`h-full rounded-full ${tone === 'danger' ? 'bg-gradient-to-r from-risk-high to-risk-critical' : 'bg-gradient-to-r from-primary to-accent'}`}
        />
      </div>
    </div>
  )
}

const ESCALATION_LABELS: Record<string, string> = {
  chief_doctor: 'ДО ГЛАВНОГО ВРАЧА',
  deputy_chief: 'ДО ЗАМ. ГЛАВНОГО ВРАЧА',
  head_of_department: 'ДО ЗАВЕДУЮЩЕГО ОТДЕЛЕНИЕМ',
}

const ROUTE_LABELS: Record<string, string> = {
  PHARMACY: 'Аптека / служба лекарственного обеспечения',
  QUALITY: 'Служба поддержки пациентов и качества медпомощи',
  EPID: 'Санитарно-эпидемиологическая служба',
}

const SEVERITY_LABELS: Record<string, string> = {
  low: 'низкий',
  medium: 'средний',
  high: 'высокий',
  critical: 'критический',
}

const ISSUE_LABELS: Record<string, string> = {
  infection: 'инфекция / вспышка',
  sterility: 'стерильность / дезинфекция',
  waste: 'медицинские отходы',
  conditions: 'санитарные условия',
}

export function AgentResult({ agentKey, payload }: { agentKey: string; payload: Record<string, any> }) {
  const meta = AGENT_BY_KEY[agentKey]
  const [expanded, setExpanded] = useState(false)
  if (!meta || agentKey === 'embedding') return null
  const Icon = meta.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="card p-4"
    >
      <div className="mb-3 flex items-center gap-2">
        <Icon className={`h-4 w-4 ${meta.color}`} />
        <h3 className="text-sm font-semibold text-navy-100">{meta.name}</h3>
      </div>

      {agentKey === 'agent1' && (
        <div className="space-y-3 text-sm">
          <p className="text-navy-200">
            Уровень: <span className="font-semibold uppercase text-navy-50">
              {RISK_LABELS[payload.risk_level as RiskLevel] ?? payload.risk_level}
            </span>
          </p>
          <ScoreBar value={payload.risk_score ?? 0} label="Уверенность" tone="danger" />
          {payload.risk_reasons?.length > 0 && (
            <ul className="space-y-1 text-xs text-navy-300">
              {payload.risk_reasons.map((r: string, i: number) => (
                <li key={i}>• {r}</li>
              ))}
            </ul>
          )}
          {payload.tags?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {payload.tags.map((t: string) => (
                <span key={t} className="rounded bg-surface-card px-2 py-0.5 text-[11px] text-navy-200">
                  {t}
                </span>
              ))}
            </div>
          )}
          {payload.escalate && payload.escalation_level && (
            <p className="rounded-lg border border-risk-critical/40 bg-risk-critical/10 px-3 py-2 text-xs font-semibold text-risk-critical">
              Эскалация: {ESCALATION_LABELS[payload.escalation_level] ?? payload.escalation_level}
            </p>
          )}
        </div>
      )}

      {agentKey === 'agent2' && (
        <div className="space-y-3 text-sm">
          {payload.is_campaign ? (
            <>
              <p className="font-semibold text-risk-high">ОБНАРУЖЕНА СКООРДИНИРОВАННАЯ КАМПАНИЯ</p>
              <ScoreBar value={payload.score ?? 0} label="Координация" tone="danger" />
              {payload.analysis && <p className="text-xs text-navy-300">{payload.analysis}</p>}
              {payload.cluster_id && (
                <Link to={`/clusters/${payload.cluster_id}`} className="text-xs text-teal-400 hover:underline">
                  Группа: {payload.cluster_name ?? `#${payload.cluster_id}`} →
                </Link>
              )}
            </>
          ) : (
            <p className="text-navy-300">✅ Скоординированных обращений не выявлено</p>
          )}
        </div>
      )}

      {agentKey === 'agent3' && (
        <div className="space-y-2 text-sm">
          {payload.is_duplicate ? (
            <>
              <p className="font-semibold text-amber-400">ДУБЛИКАТ</p>
              <ScoreBar value={payload.score ?? 0} label="Сходство" />
              <p className="text-xs text-navy-300">{payload.reason}</p>
              {payload.duplicate_of_id && (
                <Link to={`/appeals/${payload.duplicate_of_id}`} className="text-xs text-teal-400 hover:underline">
                  Оригинал: обращение #{payload.duplicate_of_id} →
                </Link>
              )}
            </>
          ) : (
            <p className="text-navy-300">✅ Оригинальное обращение, похожих не найдено</p>
          )}
        </div>
      )}

      {agentKey === 'agent4' && (
        <div className="space-y-3 text-sm">
          {payload.text || payload.confidence !== undefined ? (
            <>
              <ScoreBar value={payload.confidence ?? 0} label="Уверенность генерации" />
              {payload.legal_refs?.length > 0 && (
                <ul className="space-y-1 text-xs text-navy-300">
                  {payload.legal_refs.map((ref: { document?: string; law?: string }, i: number) => (
                    <li key={i}>§ {ref.document ?? ref.law}</li>
                  ))}
                </ul>
              )}
              {payload.text && (
                <div>
                  <button
                    onClick={() => setExpanded(!expanded)}
                    className="text-xs text-teal-400 hover:underline"
                  >
                    {expanded ? 'Свернуть проект ответа ▲' : 'Показать проект ответа ▼'}
                  </button>
                  {expanded && (
                    <p className="mt-2 whitespace-pre-wrap rounded-lg bg-surface p-3 text-xs leading-relaxed text-navy-200">
                      {payload.text}
                    </p>
                  )}
                </div>
              )}
            </>
          ) : (
            <p className="text-navy-300">Проект ответа не сформирован</p>
          )}
        </div>
      )}

      {agentKey === 'agent5' && (
        <div className="space-y-2 text-sm">
          <p className="text-navy-200">
            Профиль:{' '}
            <span className="font-semibold text-navy-50">
              {REQUESTER_CATEGORY_LABELS[payload.category] ?? payload.category ?? 'Обычный'}
            </span>
          </p>
          {(payload.score ?? 0) > 0 && <ScoreBar value={payload.score} label="Скор повторного заявителя" />}
          {payload.total_appeals_analyzed !== undefined && (
            <p className="text-xs text-navy-400">
              Проанализировано обращений: {payload.total_appeals_analyzed}
              {payload.top_topic && ` · основная тема: ${payload.top_topic}`}
            </p>
          )}
          <p className="text-[11px] leading-snug text-navy-500">
            Категория влияет только на внутреннюю маршрутизацию — обращение рассматривается по существу.
          </p>
        </div>
      )}

      {(agentKey === 'agent6' || agentKey === 'agent7') && (
        <div className="space-y-2 text-sm">
          {payload.flagged ? (
            <>
              <ScoreBar value={payload.confidence ?? 0} label="Уверенность" />
              {payload.note && <p className="text-xs text-navy-300">{payload.note}</p>}
              {payload.signals?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {payload.signals.map((s: string) => (
                    <span key={s} className="rounded bg-surface-card px-2 py-0.5 text-[11px] text-navy-200">
                      {s}
                    </span>
                  ))}
                </div>
              )}
              {payload.route_to && (
                <p className="rounded-lg border border-accent/30 bg-accent/10 px-3 py-2 text-xs font-semibold text-teal-300">
                  Маршрутизация: {ROUTE_LABELS[payload.route_to] ?? payload.route_to}
                </p>
              )}
            </>
          ) : (
            <p className="text-navy-300">✅ Профильных признаков не выявлено</p>
          )}
        </div>
      )}

      {agentKey === 'agent8' && (
        <div className="space-y-2 text-sm">
          {payload.flagged ? (
            <>
              <p className="font-semibold text-risk-high">
                Санитарно-эпидемиологический риск:{' '}
                <span className="uppercase">{SEVERITY_LABELS[payload.severity] ?? payload.severity}</span>
              </p>
              {payload.note && <p className="text-xs text-navy-300">{payload.note}</p>}
              {payload.issue_types?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {payload.issue_types.map((s: string) => (
                    <span key={s} className="rounded bg-surface-card px-2 py-0.5 text-[11px] text-navy-200">
                      {ISSUE_LABELS[s] ?? s}
                    </span>
                  ))}
                </div>
              )}
              {payload.route_to && (
                <p className="rounded-lg border border-risk-high/30 bg-risk-high/10 px-3 py-2 text-xs font-semibold text-risk-high">
                  Маршрутизация: {ROUTE_LABELS[payload.route_to] ?? payload.route_to}
                </p>
              )}
            </>
          ) : (
            <p className="text-navy-300">✅ Санитарно-эпидемиологических рисков не выявлено</p>
          )}
        </div>
      )}
    </motion.div>
  )
}
