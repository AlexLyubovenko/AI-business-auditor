"""
Модели данных для AmoCRM
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class PipelineStage(Enum):
    """Этапы воронки продаж"""
    NEW_LEAD = "Новая сделка"
    CONTACT_MADE = "Первичный контакт"
    PROPOSAL = "Отправлено КП"
    NEGOTIATION = "Переговоры"
    SUCCESS = "Успешно реализовано"
    FAILED = "Закрыто и не реализовано"


@dataclass
class Contact:
    """Контакт в AmoCRM"""
    id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_api_data(cls, data: Dict) -> 'Contact':
        """Создание объекта из данных API"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            phone=cls._extract_custom_field(data, 'PHONE'),
            email=cls._extract_custom_field(data, 'EMAIL'),
            created_at=cls._parse_datetime(data.get('created_at')),
            updated_at=cls._parse_datetime(data.get('updated_at')),
            custom_fields=data.get('custom_fields_values', []),
            tags=[tag.get('name') for tag in data.get('tags', [])]
        )

    @staticmethod
    def _extract_custom_field(data: Dict, field_type: str) -> Optional[str]:
        """Извлечение значения из кастомных полей"""
        if 'custom_fields_values' not in data:
            return None

        for field in data['custom_fields_values']:
            if field.get('field_code') == field_type:
                values = field.get('values', [])
                if values:
                    return values[0].get('value')
        return None

    @staticmethod
    def _parse_datetime(timestamp: Optional[int]) -> Optional[datetime]:
        """Парсинг timestamp в datetime"""
        if timestamp:
            return datetime.fromtimestamp(timestamp)
        return None


@dataclass
class Deal:
    """Сделка в AmoCRM"""
    id: int
    name: str
    price: Optional[float] = None
    status_id: Optional[int] = None
    pipeline_id: Optional[int] = None
    stage_id: Optional[int] = None
    stage_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    responsible_user_id: Optional[int] = None
    contacts: List[Contact] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    loss_reason: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api_data(cls, data: Dict) -> 'Deal':
        """Создание объекта из данных API"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            price=data.get('price'),
            status_id=data.get('status_id'),
            pipeline_id=data.get('pipeline_id'),
            stage_id=data.get('stage_id'),
            stage_name=cls._get_stage_name(data),
            created_at=cls._parse_datetime(data.get('created_at')),
            updated_at=cls._parse_datetime(data.get('updated_at')),
            closed_at=cls._parse_datetime(data.get('closed_at')),
            responsible_user_id=data.get('responsible_user_id'),
            contacts=[Contact.from_api_data(c) for c in
                      data.get('_embedded', {}).get('contacts', [])],
            tags=[tag.get('name') for tag in data.get('tags', [])],
            loss_reason=data.get('loss_reason'),
            custom_fields=data.get('custom_fields_values', [])
        )

    @staticmethod
    def _get_stage_name(data: Dict) -> Optional[str]:
        """Получение названия этапа"""
        if '_embedded' in data and 'status' in data['_embedded']:
            return data['_embedded']['status'].get('name')
        return None

    @staticmethod
    def _parse_datetime(timestamp: Optional[int]) -> Optional[datetime]:
        """Парсинг timestamp в datetime"""
        if timestamp:
            return datetime.fromtimestamp(timestamp)
        return None

    def is_successful(self) -> bool:
        """Проверка, успешна ли сделка"""
        return self.status_id == 142  # ID успешной сделки в AmoCRM

    def is_failed(self) -> bool:
        """Проверка, провалена ли сделка"""
        return self.status_id == 143  # ID проваленной сделки


@dataclass
class Pipeline:
    """Воронка продаж"""
    id: int
    name: str
    stages: Dict[int, str] = field(default_factory=dict)

    @classmethod
    def from_api_data(cls, data: Dict) -> 'Pipeline':
        """Создание объекта из данных API"""
        stages = {}
        for status in data.get('_embedded', {}).get('statuses', []):
            stages[status.get('id')] = status.get('name')

        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            stages=stages
        )