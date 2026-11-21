import pytest

from tsg_gateway.settings import AppEnv, Cloud, Settings


def test_defaults_to_local_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TSG_APP_ENV", raising=False)
    monkeypatch.delenv("TSG_CLOUD", raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_env is AppEnv.LOCAL
    assert settings.cloud is Cloud.LOCAL


def test_reads_prefixed_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TSG_APP_ENV", "prod")
    monkeypatch.setenv("TSG_CLOUD", "azure")

    settings = Settings(_env_file=None)

    assert settings.app_env is AppEnv.PROD
    assert settings.cloud is Cloud.AZURE
