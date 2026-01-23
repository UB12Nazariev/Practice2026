from pydantic import BaseModel, EmailStr


class OnboardEmployeeRequest(BaseModel):
    employee_email: EmailStr
    system_name: str
    organization_id: str
    collection_id: str


class OnboardEmployeeResponse(BaseModel):
    employee_email: EmailStr
    system_name: str
    bitwarden_item_id: str
    username: str
    password: str
