from services.bitwarden_vault_client import BitwardenVaultClient
from core.utils import generate_password


class OnboardingService:
    def __init__(self, bitwarden: BitwardenVaultClient):
        self.bitwarden = bitwarden

    def onboard_employee(
        self,
        employee_email: str,
        system_name: str,
        organization_id: str,
        collection_id: str,
    ) -> dict:
        password = generate_password()

        item = self.bitwarden.create_login(
            organization_id=organization_id,
            collection_id=collection_id,
            name=f"{system_name} — {employee_email}",
            username=employee_email,
            password=password,
            notes="Created by onboarding service",
        )

        return {
            "employee_email": employee_email,
            "system_name": system_name,
            "bitwarden_item_id": item["id"],
            "username": employee_email,
            "password": password,
        }
