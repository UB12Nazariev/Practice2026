from fastapi import APIRouter, Depends, HTTPException
from api.schemas.bitwarden import (
    CreateLoginRequest,
    CreateLoginResponse,
)
import logging
from deps.bitwarden import get_bitwarden_client
from services.bitwarden_vault_client import (
    BitwardenVaultClient,
    BitwardenVaultLocked,
    BitwardenVaultError,
)

router = APIRouter(
    prefix="/bitwarden",
    tags=["bitwarden"],
)

logger = logging.getLogger(__name__)


@router.post(
    "/logins",
    response_model=CreateLoginResponse,
)
def create_bitwarden_login(
    payload: CreateLoginRequest,
    client: BitwardenVaultClient = Depends(get_bitwarden_client),
):
    try:
        logger.info(f"Создание пароля BitWarden для")
        item = client.create_login(
            organization_id=payload.organization_id,
            collection_id=payload.collection_id,
            name=payload.name,
            username=payload.username,
            password=payload.password,
            notes=payload.notes,
        )
        logger.info(f"✅ Пароль BitWarden для создан!")
    except BitwardenVaultLocked:
        raise HTTPException(
            status_code=503,
            detail="Bitwarden vault is locked",
        )
    except BitwardenVaultError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Bitwarden error: {str(e)}",
        )

    return {
        "id": item["id"],
        "name": item["name"],
    }
