from services.bitwarden_vault_client import (
    BitwardenVaultClient,
    BitwardenVaultLocked,
    BitwardenVaultError,
)


def get_bitwarden_client() -> BitwardenVaultClient:
    client = BitwardenVaultClient()

    try:
        client.assert_unlocked()
    except BitwardenVaultLocked:
        # Fail fast — vault есть, но заблокирован
        raise
    except BitwardenVaultError:
        # Bitwarden вообще недоступен
        raise

    return client
