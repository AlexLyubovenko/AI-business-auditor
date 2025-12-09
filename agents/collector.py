import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import io
import json


class DataCollector:
    """Сборщик и обработчик данных из различных источников"""

    def __init__(self):
        self.supported_extensions = ['.csv', '.xlsx', '.xls', '.json', '.txt']

    def collect_from_file(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """Сбор данных из загруженного файла"""
        try:
            extension = file_name.lower().split('.')[-1]

            if extension == 'csv':
                try:
                    # Пробуем разные кодировки
                    for encoding in ['utf-8', 'cp1251', 'windows-1251', 'latin-1']:
                        try:
                            data = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # Если все кодировки не подошли, читаем как бинарный
                        data = pd.read_csv(io.BytesIO(file_content))
                except Exception as e:
                    raise Exception(f"Ошибка чтения CSV: {str(e)}")

                return self._process_dataframe(data, file_name)

            elif extension in ['xlsx', 'xls']:
                try:
                    data = pd.read_excel(io.BytesIO(file_content))
                except Exception as e:
                    raise Exception(f"Ошибка чтения Excel: {str(e)}")
                return self._process_dataframe(data, file_name)

            elif extension == 'json':
                try:
                    text_content = file_content.decode('utf-8', errors='ignore')
                    data = json.loads(text_content)
                except Exception as e:
                    raise Exception(f"Ошибка чтения JSON: {str(e)}")

                return {
                    "file_name": file_name,
                    "data_type": "json",
                    "data": data,
                    "stats": {
                        "records": len(data) if isinstance(data, list) else 1,
                        "type": "json"
                    }
                }

            elif extension == 'txt':
                try:
                    text = file_content.decode('utf-8', errors='ignore')
                except Exception as e:
                    raise Exception(f"Ошибка чтения текста: {str(e)}")

                return {
                    "file_name": file_name,
                    "data_type": "text",
                    "data": text,
                    "stats": {
                        "characters": len(text),
                        "lines": len(text.split('\n')),
                        "type": "text"
                    }
                }

            else:
                raise ValueError(f"Неподдерживаемый формат файла: {extension}")

        except Exception as e:
            raise Exception(f"Ошибка обработки файла {file_name}: {str(e)}")

    def _process_dataframe(self, df: pd.DataFrame, file_name: str) -> Dict[str, Any]:
        """Обработка DataFrame"""
        # Заменяем NaN на None для JSON сериализации
        df_cleaned = df.where(pd.notnull(df), None)

        return {
            "file_name": file_name,
            "data_type": "dataframe",
            "data": df_cleaned,
            "stats": {
                "rows": len(df),
                "columns": len(df.columns),
                "columns_list": df.columns.tolist(),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
                "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
                "text_columns": df.select_dtypes(include=['object']).columns.tolist(),
                "total_cells": len(df) * len(df.columns)
            }
        }

    def merge_multiple_sources(self, sources: List[Dict]) -> Dict[str, Any]:
        """Объединение данных из нескольких файлов"""
        dataframes = []
        text_data = []
        json_data = []

        for source in sources:
            data_type = source.get("data_type", "")

            if data_type == "dataframe":
                dataframes.append(source["data"])
            elif data_type == "text":
                text_data.append(source["data"])
            elif data_type == "json":
                json_data.append(source["data"])

        merged_df = None
        if dataframes:
            try:
                # Простое объединение по строкам
                merged_df = pd.concat(dataframes, ignore_index=True, sort=False)
            except Exception as e:
                # Если не удалось объединить, берем первый DataFrame
                merged_df = dataframes[0] if dataframes else None

        return {
            "dataframes": merged_df,
            "text_data": text_data,
            "json_data": json_data,
            "total_files": len(sources),
            "file_names": [s.get("file_name", "unknown") for s in sources],
            "data_types": [s.get("data_type", "unknown") for s in sources]
        }

    def load_file(self, file_content: bytes, file_name: str):
        """
        Универсальный метод для загрузки файла и получения DataFrame
        """
        result = self.collect_from_file(file_content, file_name)
        if result.get('data_type') == 'dataframe':
            return result['data']
        elif result.get('data_type') == 'json':
            return pd.DataFrame(result['data'])
        elif result.get('data_type') == 'text':
            # Для txt возвращаем DataFrame с одной колонкой
            return pd.DataFrame({'text': result['data'].split('\n')})
        else:
            raise Exception('Не удалось загрузить данные из файла')