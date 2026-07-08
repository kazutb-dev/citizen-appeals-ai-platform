import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { MapPin } from 'lucide-react'
import { fetchRegions } from '../api/analytics'
import { RegionalBar } from '../components/charts/RegionalBar'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import type { RegionStat } from '../types/analytics'

// Kazakhstan regions and major cities — geographic coordinates [lat, lng]
const KZ_COORDS: Record<string, [number, number]> = {
  'Астана': [51.180, 71.446],
  'Нур-Султан': [51.180, 71.446],
  'Алматы': [43.238, 76.889],
  'Шымкент': [42.317, 69.596],
  'Актобе': [50.279, 57.207],
  'Атырау': [47.122, 51.872],
  'Уральск': [51.233, 51.375],
  'Петропавловск': [54.879, 69.143],
  'Семей': [50.411, 80.256],
  'Павлодар': [52.285, 76.940],
  'Кызылорда': [44.852, 65.509],
  'Талдыкорган': [45.017, 78.374],
  'Кокшетау': [53.288, 69.392],
  'Тараз': [42.896, 71.379],
  'Туркестан': [43.298, 68.268],
  'Костанай': [53.215, 63.625],
  'Актау': [43.654, 51.198],
  'Усть-Каменогорск': [49.957, 82.612],
  'Жезказган': [47.783, 67.713],
  'Темиртау': [50.062, 72.960],
  'Балхаш': [46.854, 74.996],
  'Жанаозен': [43.333, 52.833],
  'Риддер': [50.348, 83.511],
  'Акмолинская': [51.180, 71.446],
  'Актюбинская': [50.279, 57.207],
  'Алматинская': [43.238, 76.889],
  'Атырауская': [47.122, 51.872],
  'Восточно-Казахстанская': [49.957, 82.612],
  'Жамбылская': [42.896, 71.379],
  'Карагандинская': [49.807, 73.088],
  'Костанайская': [53.215, 63.625],
  'Кызылординская': [44.852, 65.509],
  'Мангистауская': [43.654, 51.198],
  'Павлодарская': [52.285, 76.940],
  'Северо-Казахстанская': [54.879, 69.143],
  'Туркестанская': [43.298, 68.268],
  'Западно-Казахстанская': [51.233, 51.375],
  'Есильский': [51.168, 71.432],
  'Главный корпус': [51.180, 71.446],
}

function getCoords(region: string): [number, number] {
  if (KZ_COORDS[region]) return KZ_COORDS[region]
  for (const [key, coords] of Object.entries(KZ_COORDS)) {
    if (region.toLowerCase().includes(key.toLowerCase()) ||
        key.toLowerCase().includes(region.toLowerCase())) {
      return coords
    }
  }
  return [48.018, 66.924] // geographic centre of Kazakhstan
}

declare global {
  interface Window { ymaps: any }
}

function YandexMap({ regions }: { regions: RegionStat[] }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<any>(null)
  const YANDEX_KEY = (import.meta as any).env?.VITE_YANDEX_API_KEY as string | undefined

  useEffect(() => {
    if (!YANDEX_KEY || !containerRef.current) return

    const initMap = () => {
      if (!containerRef.current || mapRef.current) return
      const ymaps = window.ymaps
      if (!ymaps?.ready) return

      ymaps.ready(() => {
        if (!containerRef.current || mapRef.current) return

        const map = new ymaps.Map(containerRef.current, {
          center: [48.018, 66.924],
          zoom: 5,
          controls: ['zoomControl', 'fullscreenControl'],
        }, { suppressMapOpenBlock: true })
        mapRef.current = map

        regions.forEach(region => {
          const [lat, lng] = getCoords(region.region)
          const isCritical = region.critical > 0
          const isHot = isCritical || region.campaigns > 0

          const placemark = new ymaps.Placemark(
            [lat, lng],
            {
              balloonContentHeader: `<b>${region.region}</b>`,
              balloonContent: [
                `Обращений: <b>${region.total}</b>`,
                region.critical ? `<span style="color:#DC2626">Критических: <b>${region.critical}</b></span>` : '',
                region.escalated ? `Эскалаций: ${region.escalated}` : '',
                region.campaigns ? `Кампаний/групп: ${region.campaigns}` : '',
              ].filter(Boolean).join('<br>'),
              hintContent: `${region.region}: ${region.total} обращений`,
            },
            {
              preset: isHot
                ? 'islands#redCircleDotIconWithCaption'
                : 'islands#blueCircleDotIconWithCaption',
              iconCaptionMaxWidth: '200',
              iconCaption: String(region.total),
            }
          )
          map.geoObjects.add(placemark)
        })
      })
    }

    if (window.ymaps?.ready) {
      initMap()
    } else {
      const existing = document.getElementById('yandex-maps-script')
      if (!existing) {
        const script = document.createElement('script')
        script.id = 'yandex-maps-script'
        script.src = `https://api-maps.yandex.ru/2.1/?apikey=${YANDEX_KEY}&lang=ru_RU`
        script.onload = initMap
        document.head.appendChild(script)
      } else {
        existing.addEventListener('load', initMap)
      }
    }

    return () => {
      if (mapRef.current) {
        try { mapRef.current.destroy() } catch { /* ignore */ }
        mapRef.current = null
      }
    }
  }, [regions, YANDEX_KEY])

  if (!YANDEX_KEY) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-navy-400">
        Задайте VITE_YANDEX_API_KEY в .env для отображения карты
      </div>
    )
  }

  return <div ref={containerRef} style={{ height: 480, width: '100%' }} />
}

export function RegionalMap() {
  const { data: regions, isLoading } = useQuery({ queryKey: ['regions'], queryFn: fetchRegions })

  if (isLoading || !regions) return <LoadingSpinner label="Загрузка региональной карты…" />

  const max = Math.max(1, ...regions.map(r => r.total))

  return (
    <div className="space-y-6">
      {/* Yandex Map */}
      <div className="card overflow-hidden p-0">
        <div className="flex items-center gap-2 border-b border-border px-5 py-4">
          <MapPin className="h-4 w-4 text-teal-400" />
          <h2 className="text-sm font-semibold text-navy-100">
            Карта обращений — регионы Казахстана
          </h2>
          <span className="ml-auto text-xs text-navy-500">Нажмите на маркер для детализации</span>
        </div>
        <YandexMap regions={regions} />
      </div>

      {/* Bar chart */}
      <div className="card p-5">
        <h2 className="mb-4 text-sm font-semibold text-navy-100">
          Распределение обращений по регионам
        </h2>
        <RegionalBar data={regions} height={Math.max(360, regions.length * 34)} />
      </div>

      {/* Region cards grid */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {regions.map((r, i) => {
          const intensity = r.total / max
          const hot = r.critical > 0 || r.campaigns > 0
          return (
            <motion.div
              key={r.region}
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.03 }}
              className={`card p-4 ${hot ? 'border-risk-high/40' : ''}`}
              style={{
                background: `linear-gradient(135deg, rgba(15,108,189,${0.04 + intensity * 0.16}), rgba(13,22,39,0.9))`,
              }}
            >
              <p className="text-xs font-medium text-navy-200">{r.region}</p>
              <p className="mt-2 font-mono text-2xl font-semibold text-navy-50">{r.total}</p>
              <div className="mt-2 flex flex-wrap gap-3 text-[11px]">
                {r.critical > 0 && <span className="text-risk-critical">критич.: {r.critical}</span>}
                {r.escalated > 0 && <span className="text-risk-high">эскалац.: {r.escalated}</span>}
                {r.campaigns > 0 && <span className="text-amber-400">группы: {r.campaigns}</span>}
                {!r.critical && !r.escalated && !r.campaigns && (
                  <span className="text-navy-400">без инцидентов</span>
                )}
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}

