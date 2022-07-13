from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    db_dsn: str = "mysql+aiomysql://user:pass@host/db"
    redis_dsn: str = "redis://redis/0"
    merch_api_url: str = "http://api:8000"


class BotSettings(Settings):
    tg_bot_key: str = "dfslkjlkjk"
    tg_job_name: str = "queue_poll"
    tg_job_interval: float = 1.0
    question_age: int = 60


class CelerySettings(BaseSettings):
    db_dsn: str = "mysql+aiomysql://user:pass@host/db"
    broker_url = "redis://redis/0"
    result_backend = "redis://redis/0"
    poll_interval: int = 15
    new_offer_poll_interval: int = 29
    # ACCEPT_CONTENT = ["application/json"]
    # TASK_SERIALIZER = "json"
    # RESULT_SERIALIZER = "json"
    # TIMEZONE = "UTC"


class AdsSettings(BaseSettings):
    merchant_name: str = ""
    user_id: Optional[str]
    min_comp_spread: int = 15
    min_spread: int = 10
    interception_threshold: int = 50
    payment_comment: str = ""
    driver_url: str = "http://selenium:4444/wd/hub"
    captcha_solver_key: str
