import { api } from './client'

export interface CategoryGroup {
  label: string
  subcategories: Record<string, string>
}

export async function fetchCategories(): Promise<Record<string, CategoryGroup>> {
  const { data } = await api.get('/meta/categories')
  return data
}

export async function fetchLocations(): Promise<string[]> {
  const { data } = await api.get('/meta/locations')
  return data
}

export async function fetchRequesterTypes(): Promise<Record<string, string>> {
  const { data } = await api.get('/meta/requester-types')
  return data
}
