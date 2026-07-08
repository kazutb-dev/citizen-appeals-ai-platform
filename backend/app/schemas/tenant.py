from pydantic import BaseModel, ConfigDict


class TenantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    plan: str
    is_active: bool
    branding: dict = {}
    ai_config: dict = {}
    settings: dict = {}
    contact_email: str | None = None


class RegionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str | None = None
    center: str | None = None
    lat: float | None = None
    lng: float | None = None
    population: int | None = None


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int | None = None
    region_id: int | None = None
    name: str
    code: str | None = None
    org_type: str
    is_active: bool


class HospitalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int | None = None
    organization_id: int | None = None
    region_id: int | None = None
    name: str
    code: str | None = None
    hospital_type: str
    beds: int | None = None
    address: str | None = None
    is_active: bool
