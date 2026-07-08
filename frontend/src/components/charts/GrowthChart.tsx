import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis } from 'recharts'

/** Компактный спарклайн роста для карточек кластеров. */
export function GrowthChart({ points }: { points: { label: string; value: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={48}>
      <LineChart data={points} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
        <XAxis dataKey="label" hide />
        <Tooltip
          contentStyle={{
            background: '#111f35',
            border: '1px solid #253d60',
            borderRadius: 8,
            color: '#e2e8f0',
            fontSize: 11,
          }}
        />
        <Line type="monotone" dataKey="value" stroke="#06b6d4" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
