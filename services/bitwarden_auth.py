# services/bitwarden_auth.py
import requests
import base64
import logging
from typing import Optional, Dict
import time
import uuid
from pprint import pprint

logger = logging.getLogger(__name__)


class BitwardenAuth:
    """Класс для получения Access Token"""

    def __init__(self, client_id: str, client_secret: str, server_url: str = "https://api.bitwarden.com"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.server_url = server_url
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[float] = None

    def get_access_token(self) -> str:
        """Получить токен доступа"""
        if self.access_token and self.token_expiry and time.time() < self.token_expiry:
            return self.access_token

        return self.authenticate()

    def authenticate(self) -> str:
        try:
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_b64 = base64.b64encode(auth_string.encode()).decode()

            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            data = {
                "grant_type": "client_credentials",
                "scope": "api",
                "deviceType": "3",
                "deviceIdentifier": str(uuid.uuid4()),
                "deviceName": "FastAPI Service",
            }

            response = requests.post(
                "https://identity.bitwarden.com/connect/token",
                headers=headers,
                data=data
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.token_expiry = time.time() + token_data["expires_in"] - 60

                logger.info("✅ Успешная аутентификация в Bitwarden")
                return self.access_token
            else:
                logger.error(
                    f"❌ Ошибка аутентификации Bitwarden: "
                    f"{response.status_code} - {response.text}"
                )
                raise Exception("Bitwarden auth failed")

        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Bitwarden: {str(e)}")
            raise


def test_me(access_token: str):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(
        "https://api.bitwarden.com/organizations",
        headers=headers
    )
    try:
        if response.status_code == 200:
            print("STATUS:", response.status_code)
            return response.json()
        else:
            logger.error(
                f"❌ Ошибка аутентификации Bitwarden: "
                f"{response.status_code} - {response.text}"
            )
            raise Exception("Bitwarden auth failed")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Bitwarden: {str(e)}")
        raise


def get_org_ciphers(token: str, org_id: str):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.get(
        f"https://api.bitwarden.com/organizations/{org_id}",
        headers=headers
    )

    print("STATUS:", r.status_code)

    return r.json()


def get_collection(token: str, org_id: str):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.get(
        f"https://api.bitwarden.com/organizations/{org_id}/collections",
        headers=headers
    )

    print("STATUS:", r.status_code)

    return r.json()


def create_login_cipher(
    token: str,
    org_id: str,
    username: str,
    password: str
):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "type": [1],
        "name": f"{username}",
        "notes": "Created automatically by onboarding system",
        "organizationId": org_id,
        "collectionIds": ['ee1b460f-ff68-467d-a361-b3d600f618cc'],
        "login": {
            "username": username,
            "password": password,
            "uris": []
            # "totp": None
        }
    }

    r = requests.put(
        f"https://api.bitwarden.com/organizations/{org_id}",
        headers=headers,
        json=payload
    )

    print("STATUS:", r.status_code)
    return r.json()


auth = BitwardenAuth('user.396cc3cd-9b02-4960-9c14-b3d600f52e84', 'ysNdONU3KaZDfjSUj0hom7XZejlHTJ')
token = auth.authenticate()
print("Токен доступа: ", token[:30])

res = test_me(token)
org_id = res.get('data')[0].get('id')
print('org_id: ', org_id)
response = get_org_ciphers(token, org_id)
# pprint(response)

res2 = create_login_cipher(token, org_id, 'oknoritet', 'duhweh-5zokbe-mipmoH67626g')
pprint(res2)

collection = get_collection(token, org_id)
pprint(collection)

