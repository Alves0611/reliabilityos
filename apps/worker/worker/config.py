from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/orders"
    broker_url: str = "amqp://guest:guest@rabbitmq:5672//"
    result_backend: str = "redis://redis:6379/0"

    model_config = {"env_prefix": "WORKER_"}


settings = Settings()
