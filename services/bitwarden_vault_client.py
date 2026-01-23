import requests
from typing import Optional


class BitwardenVaultError(Exception):
    """Базовая ошибка Bitwarden Vault"""
    pass


class BitwardenVaultLocked(BitwardenVaultError):
    """Vault заблокирован"""
    pass


class BitwardenVaultClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8087",
        timeout: int = 100,
        organization_id: str = "d7821ae8-b00b-4f7a-a8bf-b3d600f618c3",
        collection_id: str = "ee1b460f-ff68-467d-a361-b3d600f618cc"
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.organization_id = organization_id
        self.collection_id = collection_id

    # -------------------------
    # Health / status
    # -------------------------
    def status(self) -> dict:
        r = requests.get(
            f"{self.base_url}/status",
            timeout=self.timeout,
        )

        r.raise_for_status()
        data = r.json()

        if not data.get("success"):
            raise BitwardenVaultError(data.get("message"))

        return data["data"]

    def assert_unlocked(self) -> None:
        status = self.status()

        if status.get("template").get('status') != "unlocked":
            raise BitwardenVaultLocked("Bitwarden vault is locked")

    # -------------------------
    # Create login (cipher)
    # -------------------------
    def create_login(
        self,
        organization_id: str,
        collection_id: str,
        name: str,
        username: str,
        password: str,
        notes: Optional[str] = None,
    ) -> dict:
        self.assert_unlocked()

        payload = {
            "organizationId": organization_id,
            "collectionIds": [collection_id],
            "folderId": None,
            "type": 1,  # Login
            "name": name,
            "notes": notes,
            "favorite": False,
            "login": {
                "username": username,
                "password": password,
                "uris": [],
                "totp": None,
            },
            "reprompt": 0,
        }

        r = requests.post(
            f"{self.base_url}/object/item",
            json=payload,
            timeout=self.timeout,
        )

        r.raise_for_status()
        data = r.json()

        if not data.get("success"):
            message = data.get("message", "Unknown Bitwarden error")

            if "locked" in message.lower():
                raise BitwardenVaultLocked(message)

            raise BitwardenVaultError(message)

        return data["data"]
