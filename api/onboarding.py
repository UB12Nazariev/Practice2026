from fastapi import APIRouter, Depends, HTTPException
from api.schemas.onboarding import (
    OnboardEmployeeRequest,
    OnboardEmployeeResponse,
)
from deps.onboarding import get_onboarding_service
from services.bitwarden_vault_client import (
    BitwardenVaultLocked,
    BitwardenVaultError,
)
from services.onboarding_service import OnboardingService

router = APIRouter(
    prefix="/onboarding",
    tags=["onboarding"],
)


@router.post(
    "/employee",
    response_model=OnboardEmployeeResponse,
)
def onboard_employee(
    payload: OnboardEmployeeRequest,
    service: OnboardingService = Depends(get_onboarding_service),
):
    try:
        return service.onboard_employee(
            employee_email=payload.employee_email,
            system_name=payload.system_name,
            organization_id=payload.organization_id,
            collection_id=payload.collection_id,
        )
    except BitwardenVaultLocked:
        raise HTTPException(
            status_code=503,
            detail="Bitwarden vault is locked",
        )
    except BitwardenVaultError as e:
        raise HTTPException(
            status_code=502,
            detail=str(e),
        )
