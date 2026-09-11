import os

class Settings:
    PROJECT_NAME: str = "AI Content Factory — LinkedIn Intelligence"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./content_factory.db")
    LINKEDIN_API_KEY: str = os.getenv("LINKEDIN_API_KEY", "")
    IS_DEMO_MODE: bool = True  # Defaults to True for safe hackathon live demo
    CACHE_TTL_SECONDS: int = 3600  # 1 hour default cache TTL
    DEFAULT_RELEVANCE_THRESHOLD: float = 0.45
    DEFAULT_REPRESENTATIVE_COUNT: int = 8

settings = Settings()

