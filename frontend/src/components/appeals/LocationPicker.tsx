import { useEffect, useRef, useState } from 'react'
import { Crosshair, Loader2, MapPin } from 'lucide-react'
import { loadYmaps } from '../../lib/ymaps'

export interface LocationValue {
  lat: number
  lng: number
  name?: string
}

interface Props {
  value: LocationValue | null
  onChange: (v: LocationValue) => void
}

const YANDEX_KEY = (import.meta as any).env?.VITE_YANDEX_API_KEY as string | undefined
const KZ_CENTER: [number, number] = [48.0196, 66.9237]

function round(n: number): number {
  return Math.round(n * 1e6) / 1e6
}

/**
 * Интерактивный выбор места обращения на карте Yandex.
 * Клик по карте / перетаскивание метки / «Моё местоположение» задают координаты.
 * При отсутствии ключа карты работает деградированный режим (геолокация / центр региона).
 */
export function LocationPicker({ value, onChange }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<any>(null)
  const markRef = useRef<any>(null)
  const ymapsRef = useRef<any>(null)
  const onChangeRef = useRef(onChange)
  onChangeRef.current = onChange

  const [status, setStatus] = useState<'loading' | 'ready' | 'error' | 'nokey'>(
    YANDEX_KEY ? 'loading' : 'nokey',
  )
  const [locating, setLocating] = useState(false)

  const reverseGeocode = async (lat: number, lng: number): Promise<string | undefined> => {
    const ymaps = ymapsRef.current
    if (!ymaps?.geocode) return undefined
    try {
      const res = await ymaps.geocode([lat, lng], { results: 1 })
      return res.geoObjects.get(0)?.getAddressLine?.() || undefined
    } catch {
      return undefined
    }
  }

  const emit = async (lat: number, lng: number) => {
    const name = await reverseGeocode(lat, lng)
    onChangeRef.current({ lat: round(lat), lng: round(lng), name })
  }

  const placeMark = (lat: number, lng: number) => {
    const ymaps = ymapsRef.current
    const map = mapRef.current
    if (!ymaps || !map) return
    if (!markRef.current) {
      markRef.current = new ymaps.Placemark(
        [lat, lng],
        { hintContent: 'Место обращения' },
        { draggable: true, preset: 'islands#redDotIcon' },
      )
      markRef.current.events.add('dragend', () => {
        const c = markRef.current.geometry.getCoordinates()
        emit(c[0], c[1])
      })
      map.geoObjects.add(markRef.current)
    } else {
      markRef.current.geometry.setCoordinates([lat, lng])
    }
  }

  // Инициализация карты (однократно).
  useEffect(() => {
    if (!YANDEX_KEY) return
    let cancelled = false
    loadYmaps(YANDEX_KEY)
      .then((ymaps) => {
        if (cancelled || !containerRef.current || mapRef.current) return
        ymapsRef.current = ymaps
        const map = new ymaps.Map(
          containerRef.current,
          {
            center: value ? [value.lat, value.lng] : KZ_CENTER,
            zoom: value ? 13 : 5,
            controls: ['zoomControl', 'fullscreenControl'],
          },
          { suppressMapOpenBlock: true },
        )
        mapRef.current = map
        map.events.add('click', (e: any) => {
          const c = e.get('coords')
          placeMark(c[0], c[1])
          emit(c[0], c[1])
        })
        if (value) placeMark(value.lat, value.lng)
        setStatus('ready')
      })
      .catch(() => {
        if (!cancelled) setStatus('error')
      })
    return () => {
      cancelled = true
      if (mapRef.current) {
        try {
          mapRef.current.destroy()
        } catch {
          /* ignore */
        }
        mapRef.current = null
      }
      markRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Синхронизация внешних изменений value (центр региона, геолокация).
  useEffect(() => {
    if (!value || !mapRef.current) return
    placeMark(value.lat, value.lng)
    const c = mapRef.current.getCenter()
    const far = Math.abs(c[0] - value.lat) > 0.25 || Math.abs(c[1] - value.lng) > 0.25
    if (far) mapRef.current.setCenter([value.lat, value.lng], Math.max(mapRef.current.getZoom(), 9))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value?.lat, value?.lng])

  const locateMe = () => {
    if (!navigator.geolocation) return
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false)
        emit(pos.coords.latitude, pos.coords.longitude)
      },
      () => setLocating(false),
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="block text-xs font-medium text-navy-300">
          Место возникновения проблемы <span className="text-risk-critical">*</span>
        </label>
        <button
          type="button"
          onClick={locateMe}
          className="flex items-center gap-1 text-xs text-teal-400 transition hover:text-teal-300"
        >
          {locating ? <Loader2 className="h-3 w-3 animate-spin" /> : <Crosshair className="h-3 w-3" />}
          Моё местоположение
        </button>
      </div>

      {status !== 'nokey' && status !== 'error' && (
        <div
          ref={containerRef}
          style={{ height: 300, width: '100%' }}
          className="overflow-hidden rounded-lg border border-border"
        />
      )}

      {(status === 'nokey' || status === 'error') && (
        <div className="rounded-lg border border-dashed border-border p-3 text-xs text-navy-400">
          Интерактивная карта недоступна. Нажмите «Моё местоположение» либо выберите «Корпус / локация» —
          координаты будут установлены по центру выбранного региона, при необходимости уточните их позже.
        </div>
      )}

      {value ? (
        <p className="flex items-start gap-1.5 text-xs text-navy-200">
          <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-teal-400" />
          <span>
            {value.name || 'Точка на карте'}
            <span className="ml-1 text-navy-500">
              ({value.lat.toFixed(5)}, {value.lng.toFixed(5)})
            </span>
          </span>
        </p>
      ) : (
        <p className="text-xs text-navy-500">
          Нажмите на карту, чтобы указать точное место, или используйте «Моё местоположение».
        </p>
      )}
    </div>
  )
}
