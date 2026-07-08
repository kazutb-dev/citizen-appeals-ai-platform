import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MapPin } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { fetchAppealsMap } from '../../api/command'
import { useLabels, RISK_KEYS, STATUS_KEYS } from '../../i18n/labels'
import { KZ_CENTER } from '../../lib/kzGeo'
import { loadYmaps } from '../../lib/ymaps'
import type { AppealMapPoint } from '../../types/situation'
import { EmptyState } from '../common/EmptyState'
import { LoadingSpinner } from '../common/LoadingSpinner'

declare global {
  interface Window { ymaps: any }
}

interface Props {
  regions: string[]
}

const YANDEX_KEY = (import.meta as any).env?.VITE_YANDEX_API_KEY as string | undefined

function getPreset(point: AppealMapPoint): string {
  if (point.risk_level === 'critical') return 'islands#redCircleDotIcon'
  if (point.risk_level === 'high') return 'islands#orangeCircleDotIcon'
  return 'islands#blueCircleDotIcon'
}

export function AppealsMapPanel({ regions }: Props) {
  const { t } = useTranslation()
  const labels = useLabels()
  const navigate = useNavigate()
  const mapRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const ymapsRef = useRef<any>(null)
  const objectsRef = useRef<any[]>([])

  const [periodHours, setPeriodHours] = useState(72)
  const [region, setRegion] = useState('')
  const [riskLevel, setRiskLevel] = useState('')
  const [status, setStatus] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['situation-map', periodHours, region, riskLevel, status],
    queryFn: () =>
      fetchAppealsMap({
        period_hours: periodHours,
        region: region || undefined,
        risk_level: riskLevel || undefined,
        status: status || undefined,
      }),
  })

  const points = useMemo(() => data ?? [], [data])

  useEffect(() => {
    if (!YANDEX_KEY || !containerRef.current || mapRef.current) return
    let disposed = false
    loadYmaps(YANDEX_KEY)
      .then((ymaps) => {
        if (disposed || !containerRef.current || mapRef.current) return
        ymapsRef.current = ymaps
        mapRef.current = new ymaps.Map(
          containerRef.current,
          {
            center: KZ_CENTER,
            zoom: 5,
            controls: ['zoomControl', 'fullscreenControl'],
          },
          { suppressMapOpenBlock: true },
        )
      })
      .catch(() => {})
    return () => {
      disposed = true
      if (mapRef.current) {
        try { mapRef.current.destroy() } catch { /* ignore */ }
        mapRef.current = null
      }
      objectsRef.current = []
    }
  }, [])

  useEffect(() => {
    if (!mapRef.current || !ymapsRef.current) return
    for (const obj of objectsRef.current) mapRef.current.geoObjects.remove(obj)
    objectsRef.current = []
    if (!points.length) {
      mapRef.current.setCenter(KZ_CENTER, 5)
      return
    }

    let latSum = 0
    let lngSum = 0
    for (const point of points) {
      latSum += point.latitude
      lngSum += point.longitude
      const placemark = new ymapsRef.current.Placemark(
        [point.latitude, point.longitude],
        {
          balloonContentHeader: `<b>#${point.id}</b>`,
          balloonContent: `${point.category_label}<br/>${point.location_name || point.region}`,
          hintContent: `${point.category_label} · ${point.region}`,
        },
        { preset: getPreset(point) },
      )
      placemark.events.add('click', () => navigate(`/appeals/${point.id}`))
      mapRef.current.geoObjects.add(placemark)
      objectsRef.current.push(placemark)
    }
    mapRef.current.setCenter([latSum / points.length, lngSum / points.length], points.length === 1 ? 12 : 5)
  }, [navigate, points])

  const regionOptions = useMemo(() => regions.filter(Boolean), [regions])

  return (
    <div className="card p-5">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-teal-400" />
            <h2 className="text-sm font-semibold text-navy-100">{t('situationOps.mapTitle')}</h2>
          </div>
          <p className="mt-1 text-xs text-navy-400">{t('situationOps.mapSubtitle')}</p>
        </div>
        <div className="text-xs text-navy-400">{t('situationOps.foundPoints', { count: points.length })}</div>
      </div>

      <div className="mb-4 grid gap-3 md:grid-cols-4">
        <select value={periodHours} onChange={(e) => setPeriodHours(Number(e.target.value))} className="input">
          <option value={24}>{t('situationOps.period24h')}</option>
          <option value={72}>{t('situationOps.period72h')}</option>
          <option value={168}>{t('situationOps.period7d')}</option>
        </select>
        <select value={region} onChange={(e) => setRegion(e.target.value)} className="input">
          <option value="">{t('situationOps.allRegions')}</option>
          {regionOptions.map((item) => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
        <select value={riskLevel} onChange={(e) => setRiskLevel(e.target.value)} className="input">
          <option value="">{t('situationOps.allRisk')}</option>
          {RISK_KEYS.map((risk) => (
            <option key={risk} value={risk}>{labels.risk(risk)}</option>
          ))}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="input">
          <option value="">{t('situationOps.allStatuses')}</option>
          {STATUS_KEYS.map((item) => (
            <option key={item} value={item}>{labels.status(item)}</option>
          ))}
        </select>
      </div>

      {!YANDEX_KEY ? (
        <EmptyState title={t('situationOps.mapUnavailableTitle')} hint={t('situationOps.mapUnavailableHint')} />
      ) : isLoading ? (
        <LoadingSpinner label={t('situationOps.loadingMap')} />
      ) : isError ? (
        <EmptyState title={t('situationOps.loadError')} hint={t('situationOps.mapLoadErrorHint')} />
      ) : !points.length ? (
        <EmptyState title={t('situationOps.mapEmptyTitle')} hint={t('situationOps.mapEmptyHint')} />
      ) : (
        <div ref={containerRef} className="overflow-hidden rounded-xl border border-border" style={{ height: 420, width: '100%' }} />
      )}
    </div>
  )
}
