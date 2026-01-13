from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str

    # File uploads
    IMAGE_UPLOAD_DIR: str = "./uploads"

    # AWS
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_S3_BUCKET: str
    
    # ADMIN
    ADMIN_USERNAME: str
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid"   # good for catching mistakes
    )

    


settings = Settings()
# print("REGION:", settings.AWS_REGION)
# print("BUCKET:", settings.AWS_S3_BUCKET)
# print("ACCESS KEY:", settings.AWS_ACCESS_KEY_ID[:6])
