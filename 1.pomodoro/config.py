import os


class Config:
    """Basic configuration shared by all environments."""

    WORK_DURATION = int(os.getenv("WORK_DURATION", "1500"))
    BREAK_DURATION = int(os.getenv("BREAK_DURATION", "300"))
    REPOSITORY_TYPE = os.getenv("REPOSITORY_TYPE", "file")
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Configuration for local development."""

    DEBUG = True


class TestConfig(Config):
    """Configuration for tests."""

    DEBUG = False
    TESTING = True
    REPOSITORY_TYPE = "memory"
    WORK_DURATION = 10
    BREAK_DURATION = 5


class ProductionConfig(Config):
    """Configuration for production."""

    DEBUG = False
    TESTING = False
