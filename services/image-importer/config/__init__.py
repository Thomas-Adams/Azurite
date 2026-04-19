from pydantic_settings import BaseSettings


DB_NAME = "azurite"
DB_SCHEMA = "imp"
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "azurite-admin"
DB_PASSWORD = "admin"
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?schema={DB_SCHEMA}"




class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "pony"
    db_user: str = "pony_admin"
    db_password: str = "admin"
    db_schema: str = "pony_image"
    service_name: str = "Azurite Image Importer"
    debug: bool = True

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_prefix = "AZURITE_"
        env_file = ".env"


# Singleton instance — imported everywhere
settings = Settings()