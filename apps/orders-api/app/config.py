from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/orders"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672//"
    app_name: str = "orders-api"

    model_config = {"env_prefix": "ORDERS_"}


settings = Settings()
