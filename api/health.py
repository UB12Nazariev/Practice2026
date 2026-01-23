from fastapi import APIRouter, HTTPException
from services.bitwarden_vault_client import BitwardenVaultClient

router = APIRouter(tags=["health"])


@router.get("/health/bitwarden")
def bitwarden_health():
    client = BitwardenVaultClient()

    try:
        status = client.status()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Bitwarden unavailable: {str(e)}",
        )

    return {
        "status": "ok",
        "vault": status,
    }
