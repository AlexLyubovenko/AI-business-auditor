"""
Аутентификация в AmoCRM через OAuth2
"""
import os
import json
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AmoCRMAuth:
    """Класс для работы с аутентификацией AmoCRM"""

    def __init__(self,
                 client_id: str,
                 client_secret: str,
                 redirect_uri: str,
                 subdomain: str):
        """
        Инициализация аутентификации

        Args:
            client_id: ID клиента из AmoCRM
            client_secret: Секретный ключ клиента
            redirect_uri: URI перенаправления (обычно https://ваш_сайт/amo_callback)
            subdomain: Поддомен вашего AmoCRM (ваш_аккаунт.amocrm.ru)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.subdomain = subdomain
        self.base_url = f"https://{subdomain}.amocrm.ru"
        self.access_token = None
        self.refresh_token = None
        self.token_expires = None

    def get_auth_url(self) -> str:
        """Получение URL для авторизации пользователя"""
        auth_url = (
            f"https://www.amocrm.ru/oauth?"
            f"client_id={self.client_id}&"
            f"state=some_state&"
            f"redirect_uri={self.redirect_uri}&"
            f"mode=post_message"
        )
        return auth_url

    def exchange_code_for_token(self, code: str) -> bool:
        """
        Обмен кода авторизации на access token

        Args:
            code: Код авторизации из callback URL

        Returns:
            bool: Успешность получения токена
        """
        token_url = f"https://{self.subdomain}.amocrm.ru/oauth2/access_token"

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }

        try:
            response = requests.post(token_url, json=data)
            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 86400)
            self.token_expires = datetime.now() + timedelta(seconds=expires_in)

            logger.info(f"✅ Токен получен. Действует до: {self.token_expires}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка получения токена: {e}")
            return False

    def refresh_access_token(self) -> bool:
        """Обновление access token с помощью refresh token"""
        if not self.refresh_token:
            logger.error("❌ Нет refresh token для обновления")
            return False

        token_url = f"https://{self.subdomain}.amocrm.ru/oauth2/access_token"

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "redirect_uri": self.redirect_uri
        }

        try:
            response = requests.post(token_url, json=data)
            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 86400)
            self.token_expires = datetime.now() + timedelta(seconds=expires_in)

            logger.info(f"✅ Токен обновлен. Действует до: {self.token_expires}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка обновления токена: {e}")
            return False

    def is_token_valid(self) -> bool:
        """Проверка валидности токена"""
        if not self.access_token or not self.token_expires:
            return False
        return datetime.now() < self.token_expires - timedelta(minutes=5)

    def get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запросов к API"""
        if not self.is_token_valid() and self.refresh_token:
            self.refresh_access_token()

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def save_tokens(self, filepath: str = "amocrm_tokens.json"):
        """Сохранение токенов в файл"""
        tokens = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.token_expires.isoformat() if self.token_expires else None
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Токены сохранены в {filepath}")

    def load_tokens(self, filepath: str = "amocrm_tokens.json"):
        """Загрузка токенов из файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tokens = json.load(f)

            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token")
            expires_at = tokens.get("expires_at")

            if expires_at:
                self.token_expires = datetime.fromisoformat(expires_at)

            logger.info(f"✅ Токены загружены из {filepath}")
            return True

        except FileNotFoundError:
            logger.warning(f"⚠️ Файл {filepath} не найден")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки токенов: {e}")
            return False