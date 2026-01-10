import json
import time
import threading
from datetime import datetime, timedelta
import requests
import logging
from typing import Optional, Dict
from abc import ABC, abstractmethod
import urllib3

logger = logging.getLogger(__name__)

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TokenStorage(ABC):
    @abstractmethod
    def save(self, tokens: Dict): pass

    @abstractmethod
    def load(self) -> Optional[Dict]: pass


class FileTokenStorage(TokenStorage):
    def __init__(self, filepath="../tokens.json"):
        self.filepath = filepath

    def save(self, tokens: Dict):
        with open(self.filepath, 'w') as f:
            json.dump(tokens, f, indent=2)

    def load(self) -> Optional[Dict]:
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None


class TokenManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, storage: TokenStorage = None):
        if not hasattr(self, 'initialized'):
            self.storage = storage or FileTokenStorage()
            self.tokens = self.storage.load() or {}
            self.refresh_lock = threading.Lock()
            self.initialized = True

    def get_access_token(self) -> str:
        """Получение валидного access_token с авто-обновлением"""
        # Если токен отсутствует или просрочен
        if not self.tokens.get('access_token') or self._is_expired():
            self._refresh_tokens()

        return self.tokens['access_token']

    def _is_expired(self) -> bool:
        """Проверка истечения срока токена"""
        if not self.tokens.get('expires_at'):
            return True

        expires_at = datetime.fromisoformat(self.tokens['expires_at'])
        # Обновляем за 5 минут до истечения
        return datetime.now() + timedelta(minutes=5) > expires_at

    def _refresh_tokens(self):
        """Обновление токенов"""
        with self.refresh_lock:
            refresh_token = self.tokens.get('refresh_token')

            if not refresh_token:
                raise ValueError("No refresh token available")

            # Запрос на обновление токена
            response = requests.post(
                "https://o2.mail.ru/token",
                data={
                    "client_id": "J34ZMt9oJv3jnx4KuSf2E5RQTxKmNbR5",
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                },
                verify=False
            )

            if response.status_code == 200:
                new_tokens = response.json()
                self._update_tokens(new_tokens)
                logger.info("Tokens refreshed successfully")
            else:
                logger.error(f"Token refresh failed: {response.text}")
                raise Exception("Token refresh failed")

    def _update_tokens(self, new_tokens: Dict):
        """Обновление токенов с сохранением"""
        expires_in = new_tokens.get('expires_in', 3600)
        new_tokens['expires_at'] = (datetime.now() +
                                    timedelta(seconds=expires_in)).isoformat()

        # Сохраняем refresh_token, если он не пришел в ответе
        if 'refresh_token' not in new_tokens:
            new_tokens['refresh_token'] = self.tokens.get('refresh_token')

        self.tokens = new_tokens
        self.storage.save(self.tokens)

    def set_tokens(self, tokens: Dict):
        """Установка новых токенов (при первой авторизации)"""
        self._update_tokens(tokens)

    def clear_tokens(self):
        """Очистка токенов (логаут)"""
        self.tokens = {}
        self.storage.save({})



