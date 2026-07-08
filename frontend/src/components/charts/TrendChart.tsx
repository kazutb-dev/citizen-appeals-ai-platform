import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TrendPoint } from '../../types/analytics'

export function TrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2563eb" stopOpacity={0.45} />
            <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="critFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#dc2626" stopOpacity={0.4} />
            <stop offset="100%" stopColor="#dc2626" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#1e3050" strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: '#64748b', fontSize: 11 }}
          tickFormatter={(d: string) => format(new Date(d), 'dd MMM', { locale: ru })}
          axisLine={{ stroke: '#1e3050' }}
          tickLine={false}
        />
        <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{
            background: '#111f35',
            border: '1px solid #253d60',
            borderRadius: 8,
            color: '#e2e8f0',
            fontSize: 12,
          }}
          labelFormatter={(d) => format(new Date(d as string), 'dd MMMM yyyy', { locale: ru })}
          formatter={(value, name) => [value as number, name === 'count' ? 'Всего' : 'Критических']}
        />
        <Area type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} fill="url(#trendFill)" />
        <Area type="monotone" dataKey="critical" stroke="#dc2626" strokeWidth={1.5} fill="url(#critFill)" />
      </AreaChart>
    </ResponsiveContainer>
  )
}
