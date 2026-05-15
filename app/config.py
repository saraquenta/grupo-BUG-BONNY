from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────
    APP_NAME: str = "MedStock Pro API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ── Base de Datos MySQL ─────────────────────────────────
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "medstock"
    DB_PASSWORD: str = "medstock123"
    DB_NAME: str = "medstock_db"

    # ── Redis ───────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── JWT ─────────────────────────────────────────────────
    SECRET_KEY: str = "medstock-super-secret-key-2026-unifranz"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas

    # ── Firebase ────────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = ""

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
