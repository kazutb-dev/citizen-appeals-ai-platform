import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MapPin } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { fetchAppealsMap } from '../../api/command'
import { useLabels, RISK_KEYS, STATUS_KEYS } from '../../i18n/labels'
import { KZ_BOUNDS, KZ_CENTER, regionBounds } from '../../lib/kzGeo'
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

const MAP_MIN_ZOOM = 5
const MAP_MAX_ZOOM = 14

function pointsBounds(points: AppealMapPoint[]): [[number, number], [number, number]] {
  let minLat = 90
  let minLng = 180
  let maxLat = -90
  let maxLng = -180
  for (const point of points) {
    minLat = Math.min(minLat, point.latitude)
    minLng = Math.min(minLng, point.longitude)
    maxLat = Math.max(maxLat, point.latitude)
    maxLng = Math.max(maxLng, point.longitude)
  }
  return [[minLat, minLng], [maxLat, maxLng]]
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
  const [hospitalId, setHospitalId] = useState<number | ''>('')
  const [riskLevel, setRiskLevel] = useState('')
  const [status, setStatus] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['situation-map', periodHours, region, hospitalId, riskLevel, status],
    queryFn: () =>
      fetchAppealsMap({
        period_hours: periodHours,
        region: region || undefined,
        hospital_id: hospitalId || undefined,
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
          {
            suppressMapOpenBlock: true,
            minZoom: MAP_MIN_ZOOM,
            maxZoom: MAP_MAX_ZOOM,
            restrictMapArea: KZ_BOUNDS,
          },
        )
        mapRef.current.options.set('minZoom', MAP_MIN_ZOOM)
        mapRef.current.options.set('maxZoom', MAP_MAX_ZOOM)
        mapRef.current.options.set('restrictMapArea', KZ_BOUNDS)
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
      if (region) {
        mapRef.current.setBounds(regionBounds(region), { checkZoomRange: true, duration: 200, zoomMargin: 18 })
      } else {
        mapRef.current.setBounds(KZ_BOUNDS, { checkZoomRange: true, duration: 200, zoomMargin: 18 })
      }
      return
    }

    for (const point of points) {
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

    if (hospitalId) {
      const focused = points.find((p) => p.hospital_id === hospitalId)
      if (focused) {
        mapRef.current.setCenter([focused.latitude, focused.longitude], 12, { duration: 220 })
        return
      }
    }

    if (region) {
      mapRef.current.setBounds(regionBounds(region), { checkZoomRange: true, duration: 220, zoomMargin: 18 })
      return
    }

    const bounds = pointsBounds(points)
    mapRef.current.setBounds(bounds, { checkZoomRange: true, duration: 220, zoomMargin: 22 })
  }, [hospitalId, navigate, points, region])

  useEffect(() => {
    if (!mapRef.current || !region || hospitalId) return
    mapRef.current.setBounds(regionBounds(region), { checkZoomRange: true, duration: 200, zoomMargin: 18 })
  }, [hospitalId, region])

  const regionOptions = useMemo(() => regions.filter(Boolean), [regions])
  const hospitalOptions = useMemo(() => {
    const map = new Map<number, string>()
    for (const point of points) {
      if (point.hospital_id && point.hospital_name && !map.has(point.hospital_id)) {
        map.set(point.hospital_id, point.hospital_name)
      }
    }
    return Array.from(map.entries())
      .map(([id, name]) => ({ id, name }))
      .sort((a, b) => a.name.localeCompare(b.name, 'ru'))
  }, [points])

  useEffect(() => {
    if (hospitalId === '') return
    if (!hospitalOptions.some((item) => item.id === hospitalId)) {
      setHospitalId('')
    }
  }, [hospitalId, hospitalOptions])

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

      <div className="mb-4 grid gap-3 md:grid-cols-5">
        <select value={periodHours} onChange={(e) => setPeriodHours(Number(e.target.value))} className="input">
          <option value={24}>{t('situationOps.period24h')}</option>
          <option value={72}>{t('situationOps.period72h')}</option>
          <option value={168}>{t('situationOps.period7d')}</option>
        </select>
        <select
          value={region}
          onChange={(e) => {
            setRegion(e.target.value)
            setHospitalId('')
          }}
          className="input"
        >
          <option value="">{t('situationOps.allCityRegions')}</option>
          {regionOptions.map((item) => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
        <select
          value={hospitalId}
          onChange={(e) => setHospitalId(e.target.value ? Number(e.target.value) : '')}
          className="input"
        >
          <option value="">{t('situationOps.allHospitals')}</option>
          {hospitalOptions.map((item) => (
            <option key={item.id} value={item.id}>{item.name}</option>
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
      ) : (
        <div className="space-y-3">
          <div ref={containerRef} className="overflow-hidden rounded-xl border border-border" style={{ height: 420, width: '100%' }} />
          {!points.length && (
            <EmptyState title={t('situationOps.mapEmptyTitle')} hint={t('situationOps.mapEmptyHint')} />
          )}
        </div>
      )}
    </div>
  )
}
