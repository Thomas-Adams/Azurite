from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AZURITE_", env_file=".env")
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "pony"
    db_user: str = "pony_admin"
    db_password: str = "admin"
    db_schema: str = "pony_image"
    image_root: str = "/mnt/windows/stablediffusion"
    debug: bool = True
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "tsukuyomi"
    meili_host: str = "http://localhost:7700"
    meili_api_key: str = ""
    meili_index: str = "images"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()