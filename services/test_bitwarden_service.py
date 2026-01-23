from services.bitwarden_vault_client import BitwardenVaultClient

ORG_ID = "d7821ae8-b00b-4f7a-a8bf-b3d600f618c3"
COLLECTION_ID = "ee1b460f-ff68-467d-a361-b3d600f618cc"

client = BitwardenVaultClient()

print("Vault status:", client.status())

item = client.create_login(
    organization_id=ORG_ID,
    collection_id=COLLECTION_ID,
    name="Onboarding Test Login",
    username="new.employee",
    password="TempPassword-123!",
    notes="Created by onboarding service",
)

print("Created item ID:", item["id"])
