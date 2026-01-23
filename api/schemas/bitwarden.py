from pydantic import BaseModel, Field
from typing import Optional


class CreateLoginRequest(BaseModel):
    organization_id: str = Field(..., description="Bitwarden organization ID")
    collection_id: str = Field(..., description="Bitwarden collection ID")
    name: str = Field(..., description="Login name in Bitwarden")
    username: str = Field(..., description="Login username")
    password: str = Field(..., description="Login password")
    notes: Optional[str] = Field(None, description="Optional notes")


class CreateLoginResponse(BaseModel):
    id: str
    name: str
