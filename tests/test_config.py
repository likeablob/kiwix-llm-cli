"""Tests for kiwix-llm-cli configuration"""

from pathlib import Path

from kiwix_llm_cli.config import Settings, create_default_config


def test_settings_defaults():
    settings = Settings.load(ignore_config=True)
    assert settings.default_zim is None
    assert settings.backend == "libzim"
    assert settings.kiwix_api_url == "http://localhost:8080"


def test_backend_config():
    settings = Settings.load(ignore_config=True)
    settings.backend = "api"
    assert settings.backend == "api"


def test_kiwix_api_url_config():
    settings = Settings.load(ignore_config=True)
    settings.kiwix_api_url = "http://custom:9999"
    assert settings.kiwix_api_url == "http://custom:9999"


def test_settings_env_backend(monkeypatch):
    monkeypatch.setenv("KWXLC_BACKEND", "api")
    settings = Settings.load(ignore_config=True)
    assert settings.backend == "api"


def test_settings_env_kiwix_api_url(monkeypatch):
    monkeypatch.setenv("KWXLC_KIWIX_API_URL", "http://custom:9999")
    settings = Settings.load(ignore_config=True)
    assert settings.kiwix_api_url == "http://custom:9999"


def test_settings_env_default_zim(monkeypatch):
    monkeypatch.setenv("KWXLC_DEFAULT_ZIM", "wikipedia_ja")
    settings = Settings.load(ignore_config=True)
    assert settings.default_zim == "wikipedia_ja"


def test_create_default_config():
    config_text = create_default_config()
    assert "default_zim:" in config_text
    assert "backend:" in config_text
    assert "kiwix_api_url:" in config_text
    assert "search_dirs:" in config_text


def test_get_search_dirs(tmp_path: Path):
    settings = Settings.load(ignore_config=True)
    settings.search_dirs = [str(tmp_path)]

    zim_file = tmp_path / "test.zim"
    zim_file.touch()

    dirs = settings.get_search_dirs()
    assert tmp_path in dirs


def test_get_download_dir():
    settings = Settings.load(ignore_config=True)
    settings.download_dir = "~/custom"
    dir = settings.get_download_dir()
    assert "custom" in str(dir)


def test_local_config_name():
    from kiwix_llm_cli.config import LOCAL_CONFIG_FILE

    assert LOCAL_CONFIG_FILE.name == ".kiwix-llm-cli.yaml"
