"""
Основной клиент для работы с AmoCRM API
"""
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from .auth import AmoCRMAuth
from .models import Deal, Contact, Pipeline

logger = logging.getLogger(__name__)


class AmoCRMClient:
    """Клиент для работы с AmoCRM API"""

    def __init__(self, auth: AmoCRMAuth):
        """
        Инициализация клиента

        Args:
            auth: Объект аутентификации AmoCRMAuth
        """
        self.auth = auth
        self.base_url = f"https://{auth.subdomain}.amocrm.ru/api/v4"

    def _make_request(self,
                      method: str,
                      endpoint: str,
                      params: Optional[Dict] = None,
                      data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Выполнение запроса к AmoCRM API

        Args:
            method: HTTP метод (GET, POST, PATCH)
            endpoint: Endpoint API
            params: Query параметры
            data: Тело запроса

        Returns:
            Ответ API или None при ошибке
        """
        url = f"{self.base_url}/{endpoint}"
        headers = self.auth.get_headers()

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, params=params, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, params=params, json=data)
            else:
                logger.error(f"❌ Неподдерживаемый метод: {method}")
                return None

            response.raise_for_status()

            # Для запросов без тела возвращаем пустой словарь
            if response.status_code == 204:
                return {}

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка запроса к {url}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Ответ сервера: {e.response.text}")
            return None

    # ========== МЕТОДЫ ДЛЯ РАБОТЫ СО СДЕЛКАМИ ==========

    def get_deals(self,
                  pipeline_id: Optional[int] = None,
                  status_id: Optional[int] = None,
                  responsible_user_id: Optional[int] = None,
                  limit: int = 250,
                  page: int = 1) -> List[Deal]:
        """
        Получение списка сделок

        Args:
            pipeline_id: ID воронки
            status_id: ID статуса
            responsible_user_id: ID ответственного
            limit: Лимит сделок на страницу (макс 250)
            page: Номер страницы

        Returns:
            Список объектов Deal
        """
        endpoint = "leads"
        params = {
            "limit": min(limit, 250),
            "page": page,
            "with": "contacts,loss_reason"
        }

        if pipeline_id:
            params["filter[pipeline_id][]"] = pipeline_id
        if status_id:
            params["filter[status_id][]"] = status_id
        if responsible_user_id:
            params["filter[responsible_user_id][]"] = responsible_user_id

        response = self._make_request("GET", endpoint, params=params)
        if not response:
            return []

        deals = []
        for deal_data in response.get("_embedded", {}).get("leads", []):
            deals.append(Deal.from_api_data(deal_data))

        logger.info(f"✅ Получено {len(deals)} сделок")
        return deals

    def get_deal_by_id(self, deal_id: int) -> Optional[Deal]:
        """Получение сделки по ID"""
        endpoint = f"leads/{deal_id}"
        params = {"with": "contacts,loss_reason"}

        response = self._make_request("GET", endpoint, params=params)
        if not response:
            return None

        return Deal.from_api_data(response)

    def get_deals_in_date_range(self,
                                start_date: datetime,
                                end_date: datetime,
                                **kwargs) -> List[Deal]:
        """
        Получение сделок за определенный период

        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            **kwargs: Дополнительные параметры для get_deals

        Returns:
            Список сделок за период
        """
        all_deals = []
        page = 1

        while True:
            deals = self.get_deals(page=page, **kwargs)
            if not deals:
                break

            filtered_deals = []
            for deal in deals:
                if deal.created_at and start_date <= deal.created_at <= end_date:
                    filtered_deals.append(deal)

            all_deals.extend(filtered_deals)

            # Если самая старая сделка на странице старше start_date, продолжаем
            if deals and deals[-1].created_at and deals[-1].created_at < start_date:
                page += 1
            else:
                break

        logger.info(f"✅ Найдено {len(all_deals)} сделок за период "
                    f"{start_date.date()} - {end_date.date()}")
        return all_deals

    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С КОНТАКТАМИ ==========

    def get_contacts(self,
                     limit: int = 250,
                     page: int = 1) -> List[Contact]:
        """Получение списка контактов"""
        endpoint = "contacts"
        params = {
            "limit": min(limit, 250),
            "page": page,
            "with": "leads"
        }

        response = self._make_request("GET", endpoint, params=params)
        if not response:
            return []

        contacts = []
        for contact_data in response.get("_embedded", {}).get("contacts", []):
            contacts.append(Contact.from_api_data(contact_data))

        logger.info(f"✅ Получено {len(contacts)} контактов")
        return contacts

    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С ВОРОНКАМИ ==========

    def get_pipelines(self) -> List[Pipeline]:
        """Получение списка воронок"""
        endpoint = "leads/pipelines"

        response = self._make_request("GET", endpoint)
        if not response:
            return []

        pipelines = []
        for pipeline_data in response.get("_embedded", {}).get("pipelines", []):
            pipelines.append(Pipeline.from_api_data(pipeline_data))

        logger.info(f"✅ Получено {len(pipelines)} воронок")
        return pipelines

    def get_pipeline_by_id(self, pipeline_id: int) -> Optional[Pipeline]:
        """Получение воронки по ID"""
        endpoint = f"leads/pipelines/{pipeline_id}"

        response = self._make_request("GET", endpoint)
        if not response:
            return None

        return Pipeline.from_api_data(response)

    # ========== МЕТОДЫ ДЛЯ АНАЛИТИКИ ==========

    def analyze_sales_funnel(self,
                             pipeline_id: Optional[int] = None,
                             days: int = 30) -> Dict[str, Any]:
        """
        Анализ воронки продаж

        Args:
            pipeline_id: ID воронки (если None - все воронки)
            days: Количество дней для анализа

        Returns:
            Словарь с анализом воронки
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Получаем сделки за период
        deals = self.get_deals_in_date_range(
            start_date=start_date,
            end_date=end_date,
            pipeline_id=pipeline_id
        )

        if not deals:
            return {"error": "Нет сделок для анализа"}

        # Анализируем воронку
        pipeline = None
        if pipeline_id:
            pipeline = self.get_pipeline_by_id(pipeline_id)

        return self._calculate_funnel_metrics(deals, pipeline)

    def _calculate_funnel_metrics(self,
                                  deals: List[Deal],
                                  pipeline: Optional[Pipeline]) -> Dict[str, Any]:
        """Расчет метрик воронки"""
        # Группировка сделок по этапам
        stages_data = {}
        successful_deals = []
        failed_deals = []

        for deal in deals:
            stage_id = deal.stage_id
            if stage_id:
                if stage_id not in stages_data:
                    stages_data[stage_id] = {
                        "name": deal.stage_name or f"Этап {stage_id}",
                        "count": 0,
                        "total_value": 0,
                        "deals": []
                    }

                stages_data[stage_id]["count"] += 1
                stages_data[stage_id]["total_value"] += (deal.price or 0)
                stages_data[stage_id]["deals"].append(deal.id)

            if deal.is_successful():
                successful_deals.append(deal)
            elif deal.is_failed():
                failed_deals.append(deal)

        # Расчет конверсии
        total_deals = len(deals)
        conversion_rate = 0
        if total_deals > 0:
            conversion_rate = (len(successful_deals) / total_deals) * 100

        # Расчет средней суммы сделки
        total_value = sum(deal.price or 0 for deal in deals if deal.price)
        avg_deal_value = total_value / len(deals) if deals else 0

        # Поиск узких мест
        bottlenecks = self._find_bottlenecks(stages_data)

        # Подготовка результата
        result = {
            "period": {
                "start": min(d.created_at for d in deals if d.created_at).isoformat(),
                "end": max(d.created_at for d in deals if d.created_at).isoformat()
            },
            "summary": {
                "total_deals": total_deals,
                "successful_deals": len(successful_deals),
                "failed_deals": len(failed_deals),
                "conversion_rate": round(conversion_rate, 2),
                "total_value": round(total_value, 2),
                "avg_deal_value": round(avg_deal_value, 2)
            },
            "stages": stages_data,
            "bottlenecks": bottlenecks,
            "successful_deals_ids": [d.id for d in successful_deals],
            "failed_deals_ids": [d.id for d in failed_deals]
        }

        if pipeline:
            result["pipeline"] = {
                "id": pipeline.id,
                "name": pipeline.name
            }

        return result

    def _find_bottlenecks(self, stages_data: Dict) -> List[Dict]:
        """Поиск узких мест в воронке"""
        bottlenecks = []
        stage_ids = list(stages_data.keys())

        for i in range(len(stage_ids) - 1):
            current_stage = stages_data[stage_ids[i]]
            next_stage = stages_data[stage_ids[i + 1]]

            current_count = current_stage["count"]
            next_count = next_stage["count"]

            if current_count > 0:
                conversion = (next_count / current_count) * 100

                if conversion < 30:  # Низкая конверсия - узкое место
                    bottlenecks.append({
                        "from_stage": current_stage["name"],
                        "to_stage": next_stage["name"],
                        "conversion_rate": round(conversion, 2),
                        "lost_deals": current_count - next_count,
                        "severity": "high" if conversion < 20 else "medium"
                    })

        return bottlenecks

    def get_manager_performance(self, days: int = 30) -> Dict[int, Dict]:
        """
        Анализ эффективности менеджеров

        Args:
            days: Количество дней для анализа

        Returns:
            Словарь с эффективностью каждого менеджера
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        deals = self.get_deals_in_date_range(start_date, end_date)

        managers = {}
        for deal in deals:
            manager_id = deal.responsible_user_id
            if not manager_id:
                continue

            if manager_id not in managers:
                managers[manager_id] = {
                    "total_deals": 0,
                    "successful_deals": 0,
                    "failed_deals": 0,
                    "total_value": 0,
                    "avg_deal_time": 0,
                    "deals": []
                }

            managers[manager_id]["total_deals"] += 1
            managers[manager_id]["total_value"] += (deal.price or 0)
            managers[manager_id]["deals"].append(deal.id)

            if deal.is_successful():
                managers[manager_id]["successful_deals"] += 1
            elif deal.is_failed():
                managers[manager_id]["failed_deals"] += 1

            # Расчет времени сделки
            if deal.created_at and deal.closed_at:
                deal_time = (deal.closed_at - deal.created_at).days
                managers[manager_id]["avg_deal_time"] = \
                    (managers[manager_id]["avg_deal_time"] + deal_time) / 2

        # Расчет дополнительных метрик
        for manager_id, data in managers.items():
            if data["total_deals"] > 0:
                data["conversion_rate"] = \
                    (data["successful_deals"] / data["total_deals"]) * 100
                data["avg_deal_value"] = \
                    data["total_value"] / data["total_deals"]
            else:
                data["conversion_rate"] = 0
                data["avg_deal_value"] = 0

        return managers