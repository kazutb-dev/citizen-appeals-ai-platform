import { useMutation, useQuery } from '@tanstack/react-query'
import { Loader2, Paperclip, Send, X } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitAppeal, uploadAttachment } from '../api/appeals'
import { fetchCategories, fetchLocations } from '../api/meta'
import { LocationPicker, type LocationValue } from '../components/appeals/LocationPicker'
import { regionCenter } from '../lib/kzGeo'

const MAX_FILES = 5

export function SubmitAppeal() {
  const navigate = useNavigate()
  const { data: categories } = useQuery({ queryKey: ['meta-categories'], queryFn: fetchCategories })
  const { data: locations } = useQuery({ queryKey: ['meta-locations'], queryFn: fetchLocations })

  const [form, setForm] = useState({
    title: '',
    text: '',
    category: '',
    subcategory: '',
    region: '',
    district: '',
  })
  const [files, setFiles] = useState<File[]>([])
  const [location, setLocation] = useState<LocationValue | null>(null)
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: async () => {
      const appeal = await submitAppeal({
        title: form.title,
        text: form.text,
        category: form.category,
        subcategory: form.subcategory || undefined,
        region: form.region,
        district: form.district || undefined,
        latitude: location!.lat,
        longitude: location!.lng,
        location_name: location?.name || form.region || undefined,
      })
      for (const file of files) {
        await uploadAttachment(appeal.id, file)
      }
      return appeal
    },
    onSuccess: (appeal) => navigate(`/appeal/${appeal.id}`),
    onError: (err: any) =>
      setError(err?.response?.data?.detail ?? 'Не удалось отправить обращение'),
  })

  const subcategories = form.category && categories
    ? Object.entries(categories[form.category]?.subcategories ?? {})
    : []

  const addFiles = (list: FileList | null) => {
    if (!list) return
    setFiles((prev) => [...prev, ...Array.from(list)].slice(0, MAX_FILES))
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-navy-50">Подать обращение</h1>
        <p className="mt-1 text-sm text-navy-400">
          Опишите вопрос — система направит его в ответственное подразделение медицинской организации.
          Ход рассмотрения можно отслеживать в разделе «Мои обращения».
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          setError('')
          if (!location) {
            setError('Укажите место возникновения проблемы на карте')
            return
          }
          mutation.mutate()
        }}
        className="card space-y-4 p-6"
      >
        <div>
          <label className="mb-1.5 block text-xs font-medium text-navy-300">Тема обращения</label>
          <input
            required
            minLength={3}
            maxLength={500}
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="input w-full"
            placeholder="Кратко: о чём обращение"
          />
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-navy-300">Категория</label>
            <select
              required
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value, subcategory: '' })}
              className="input w-full"
            >
              <option value="">Выберите категорию</option>
              {categories &&
                Object.entries(categories).map(([key, group]) => (
                  <option key={key} value={key}>{group.label}</option>
                ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-navy-300">Подкатегория</label>
            <select
              value={form.subcategory}
              onChange={(e) => setForm({ ...form, subcategory: e.target.value })}
              className="input w-full"
              disabled={!subcategories.length}
            >
              <option value="">{subcategories.length ? 'Уточните вопрос' : '—'}</option>
              {subcategories.map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-navy-300">Корпус / локация</label>
            <select
              required
              value={form.region}
              onChange={(e) => {
                const region = e.target.value
                setForm({ ...form, region })
                setLocation((prev) => {
                  if (prev) return prev
                  const [lat, lng] = regionCenter(region)
                  return { lat, lng, name: region }
                })
              }}
              className="input w-full"
            >
              <option value="">Где возник вопрос</option>
              {locations?.map((loc) => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-navy-300">Аудитория / комната</label>
            <input
              value={form.district}
              onChange={(e) => setForm({ ...form, district: e.target.value })}
              className="input w-full"
              placeholder="необязательно"
            />
          </div>
        </div>

        <LocationPicker value={location} onChange={setLocation} />

        <div>
          <label className="mb-1.5 block text-xs font-medium text-navy-300">Текст обращения</label>
          <textarea
            required
            minLength={10}
            maxLength={20000}
            rows={8}
            value={form.text}
            onChange={(e) => setForm({ ...form, text: e.target.value })}
            className="input w-full resize-y"
            placeholder="Опишите ситуацию подробно: что произошло, когда, какие шаги уже предпринимались…"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-navy-300">
            Вложения (PDF, DOCX, изображения; до {MAX_FILES} файлов по 10 МБ)
          </label>
          <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-border px-4 py-3 text-sm text-navy-300 transition hover:border-border-light hover:text-navy-100">
            <Paperclip className="h-4 w-4" />
            Прикрепить файлы
            <input
              type="file"
              multiple
              className="hidden"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.txt"
              onChange={(e) => addFiles(e.target.files)}
            />
          </label>
          {files.length > 0 && (
            <ul className="mt-2 space-y-1">
              {files.map((f, i) => (
                <li key={`${f.name}-${i}`} className="flex items-center gap-2 text-xs text-navy-200">
                  <Paperclip className="h-3 w-3 text-navy-400" />
                  {f.name}
                  <span className="text-navy-500">({Math.round(f.size / 1024)} КБ)</span>
                  <button
                    type="button"
                    onClick={() => setFiles(files.filter((_, j) => j !== i))}
                    className="text-navy-400 hover:text-risk-critical"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {error && (
          <p className="rounded-lg border border-risk-critical/40 bg-risk-critical/10 px-3 py-2 text-xs text-risk-critical">
            {error}
          </p>
        )}

        <button type="submit" disabled={mutation.isPending || !location} className="btn-primary w-full justify-center">
          {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          Отправить обращение
        </button>
      </form>
    </div>
  )
}
