"""Config tests do not connect to Oracle."""
from app.core.config import Settings

def test_cors_parsing():
    settings = Settings(_env_file=None, CORS_ORIGINS="http://localhost:5173, http://localhost:5500")
    assert settings.cors_origins == ["http://localhost:5173", "http://localhost:5500"]

def test_missing_db_config():
    settings = Settings(_env_file=None, DB_USER="", DB_PASSWORD="", DB_SERVICE="")
    try:
        settings.require_database()
    except RuntimeError as exc:
        assert "DB_USER" in str(exc)
    else:
        raise AssertionError("Expected missing DB configuration error")
