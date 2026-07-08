// Единый загрузчик Yandex Maps JS API 2.1 (idempotent, для карт и геовыбора).
declare global {
  interface Window {
    ymaps: any
  }
}

let loaderPromise: Promise<any> | null = null

/**
 * Загружает Yandex Maps один раз и резолвит `window.ymaps` после `ready`.
 * Повторные вызовы переиспользуют тот же промис.
 */
export function loadYmaps(apiKey: string): Promise<any> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('window недоступен'))
  }
  if (window.ymaps?.ready) {
    return new Promise((resolve) => window.ymaps.ready(() => resolve(window.ymaps)))
  }
  if (loaderPromise) return loaderPromise

  loaderPromise = new Promise((resolve, reject) => {
    const onReady = () => {
      if (window.ymaps?.ready) window.ymaps.ready(() => resolve(window.ymaps))
      else reject(new Error('Yandex Maps не инициализировался'))
    }
    const existing = document.getElementById('yandex-maps-script') as HTMLScriptElement | null
    if (existing) {
      existing.addEventListener('load', onReady)
      existing.addEventListener('error', () => reject(new Error('Ошибка загрузки Yandex Maps')))
      return
    }
    const script = document.createElement('script')
    script.id = 'yandex-maps-script'
    script.src = `https://api-maps.yandex.ru/2.1/?apikey=${apiKey}&lang=ru_RU`
    script.async = true
    script.onload = onReady
    script.onerror = () => reject(new Error('Ошибка загрузки Yandex Maps'))
    document.head.appendChild(script)
  })
  return loaderPromise
}
