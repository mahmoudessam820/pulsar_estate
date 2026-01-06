from app.config.settings import settings


def test_settings_loaded():
    assert settings.app_name == "PulsarEstate"
