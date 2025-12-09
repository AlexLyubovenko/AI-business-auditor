# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # App settings
    MAX_FILE_SIZE_MB = 200
    SUPPORTED_EXTENSIONS = ['.csv', '.xlsx', '.xls', '.json', '.txt', '.pdf']

    # Analysis settings
    DEFAULT_ANALYSIS_TYPE = "comprehensive"
    ENABLE_LLM_ANALYSIS = True

    # Paths
    REPORTS_DIR = "reports"
    UPLOADS_DIR = "uploads"

    @classmethod
    def create_dirs(cls):
        """Создание необходимых директорий"""
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)
        os.makedirs(cls.UPLOADS_DIR, exist_ok=True)