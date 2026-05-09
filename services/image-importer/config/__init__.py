from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AZURITE_", env_file=".env")
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "pony"
    db_user: str = "pony_admin"
    db_password: str = "admin"
    db_schema: str = "pony_image"
    debug: bool = True
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "tsukuyomi"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()