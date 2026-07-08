import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { RegionStat } from '../../types/analytics'

export function RegionalBar({ data, height = 360 }: { data: RegionStat[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 12, left: 40, bottom: 0 }}>
        <CartesianGrid stroke="#1e3050" strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="region"
          width={150}
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: 'rgba(37, 99, 235, 0.06)' }}
          contentStyle={{
            background: '#111f35',
            border: '1px solid #253d60',
            borderRadius: 8,
            color: '#e2e8f0',
            fontSize: 12,
          }}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <Bar dataKey="total" name="Всего" fill="#2563eb" radius={[0, 4, 4, 0]} barSize={10} />
        <Bar dataKey="critical" name="Критических" fill="#dc2626" radius={[0, 4, 4, 0]} barSize={10} />
        <Bar dataKey="campaigns" name="Группы" fill="#ea580c" radius={[0, 4, 4, 0]} barSize={10} />
      </BarChart>
    </ResponsiveContainer>
  )
}
