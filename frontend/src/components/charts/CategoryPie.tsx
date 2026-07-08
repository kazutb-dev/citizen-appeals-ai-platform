import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { CategoryStat } from '../../types/analytics'
import { useLabels } from '../../i18n/labels'

const COLORS = [
  '#2563eb', '#06b6d4', '#16a34a', '#d97706', '#dc2626', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f59e0b', '#6366f1', '#84cc16', '#f43f5e', '#64748b',
]

export function CategoryPie({ data }: { data: CategoryStat[] }) {
  const labels = useLabels()
  const chartData = data.map((d) => ({
    name: labels.category(d.category),
    value: d.count,
  }))
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="value"
          nameKey="name"
          innerRadius={55}
          outerRadius={90}
          paddingAngle={2}
          stroke="#0d1627"
        >
          {chartData.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: '#111f35',
            border: '1px solid #253d60',
            borderRadius: 8,
            color: '#e2e8f0',
            fontSize: 12,
          }}
        />
        <Legend
          wrapperStyle={{ fontSize: 11, color: '#94a3b8' }}
          iconType="circle"
          iconSize={8}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
