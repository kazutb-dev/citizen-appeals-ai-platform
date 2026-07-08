// Координаты административных центров регионов РК (для карты и геовыбора).
// Имена совпадают с backend app/data/departments_data.py -> KZ_REGIONS.
export const KZ_REGION_COORDS: Record<string, [number, number]> = {
  'Астана': [51.1605, 71.4704],
  'Алматы': [43.222, 76.8512],
  'Шымкент': [42.3417, 69.5901],
  'Абайская область': [50.4111, 80.2275],
  'Акмолинская область': [53.2872, 69.39],
  'Актюбинская область': [50.2839, 57.167],
  'Алматинская область': [43.86, 77.07],
  'Атырауская область': [47.0945, 51.9238],
  'Восточно-Казахстанская область': [49.9481, 82.6279],
  'Жамбылская область': [42.9, 71.3667],
  'Жетысуская область': [45.0156, 78.3739],
  'Западно-Казахстанская область': [51.227, 51.3865],
  'Карагандинская область': [49.8047, 73.1094],
  'Костанайская область': [53.2144, 63.6246],
  'Кызылординская область': [44.8488, 65.4823],
  'Мангистауская область': [43.641, 51.198],
  'Павлодарская область': [52.287, 76.9674],
  'Северо-Казахстанская область': [54.8666, 69.15],
  'Туркестанская область': [43.3017, 68.2517],
  'Улытауская область': [47.7833, 67.7],
}

// Географический центр Казахстана — запасные координаты.
export const KZ_CENTER: [number, number] = [48.0196, 66.9237]

// Границы Казахстана для ограничения operational-карты.
export const KZ_BOUNDS: [[number, number], [number, number]] = [
  [40.4, 46.2],
  [55.9, 87.4],
]

/** Координаты центра региона по имени (с нечётким совпадением); иначе — центр РК. */
export function regionCenter(name?: string | null): [number, number] {
  if (!name) return KZ_CENTER
  if (KZ_REGION_COORDS[name]) return KZ_REGION_COORDS[name]
  for (const [key, coords] of Object.entries(KZ_REGION_COORDS)) {
    if (name.includes(key) || key.includes(name)) return coords
  }
  return KZ_CENTER
}

/** Квадрат фокуса вокруг центра региона: подходит для auto-fit города/области. */
export function regionBounds(name?: string | null, radiusDeg = 0.55): [[number, number], [number, number]] {
  const [lat, lng] = regionCenter(name)
  return [
    [lat - radiusDeg, lng - radiusDeg],
    [lat + radiusDeg, lng + radiusDeg],
  ]
}
