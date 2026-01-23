from deps.bitwarden import get_bitwarden_client
from services.onboarding_service import OnboardingService


def get_onboarding_service() -> OnboardingService:
    bitwarden = get_bitwarden_client()
    return OnboardingService(bitwarden)
