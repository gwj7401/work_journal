# -*- coding: utf-8 -*-
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_secret_key: str = "dev-secret-key-change-in-production"
    app_env: str = "development"

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "Szs123456@"
    db_name: str = "work_journal_db"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    jwt_expire_minutes: int = 10080  # 7 days

    dept_name: str = "质量技术部"

    @property
    def database_url(self) -> str:
        from urllib.parse import quote_plus
        pwd = quote_plus(self.db_password)   # 转义 @ & 等特殊字符
        return (
            f"mysql+pymysql://{self.db_user}:{pwd}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
