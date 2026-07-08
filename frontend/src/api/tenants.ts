import { api } from './client'

export interface RegionInfo {
  id: number
  name: string
  code: string | null
  center: string | null
  lat: number | null
  lng: number | null
  population: number | null
}

export interface HospitalInfo {
  id: number
  tenant_id: number | null
  organization_id: number | null
  region_id: number | null
  name: string
  code: string | null
  hospital_type: string
  beds: number | null
  address: string | null
  is_active: boolean
}

export interface OrganizationInfo {
  id: number
  tenant_id: number | null
  region_id: number | null
  name: string
  code: string | null
  org_type: string
  is_active: boolean
}

export interface TenantInfo {
  id: number
  name: string
  slug: string
  plan: string
  is_active: boolean
  branding: Record<string, unknown>
  ai_config: Record<string, unknown>
  settings: Record<string, unknown>
  contact_email: string | null
}

export async function fetchRegions(): Promise<RegionInfo[]> {
  const { data } = await api.get('/tenants/regions')
  return data
}

export async function fetchHospitals(regionId?: number): Promise<HospitalInfo[]> {
  const { data } = await api.get('/tenants/hospitals', {
    params: regionId ? { region_id: regionId } : {},
  })
  return data
}

export async function fetchOrganizations(): Promise<OrganizationInfo[]> {
  const { data } = await api.get('/tenants/organizations')
  return data
}

export async function fetchTenants(): Promise<TenantInfo[]> {
  const { data } = await api.get('/tenants')
  return data
}
