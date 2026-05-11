import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=False)


class Settings(BaseSettings):
    google_genai_use_vertexai: bool = True
    google_cloud_project: str = "rapid-idiom-488010-b2"
    google_cloud_location: str = "us-central1"
    gemini_model: str = "gemini-2.5-pro-preview"
    host: str = "127.0.0.1"
    a2a_agent_host: str = "127.0.0.1"
    port: int = 8000
    a2a_safety_port: int = 8001
    chroma_persist_dir: Path = ROOT_DIR / "backend" / "data" / "chroma"
    frontend_origin: str = "http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def backend_base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def safety_agent_card_url(self) -> str:
        return f"http://{self.a2a_agent_host}:{self.a2a_safety_port}/.well-known/agent-card.json"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def apply_google_runtime_env(settings: Settings) -> None:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = (
        "TRUE" if settings.google_genai_use_vertexai else "FALSE"
    )
    os.environ["GOOGLE_CLOUD_PROJECT"] = settings.google_cloud_project
    os.environ["GOOGLE_CLOUD_LOCATION"] = settings.google_cloud_location
