import os

import pytest

from app.server import get_server_config


def test_get_server_config_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)

    config = get_server_config()

    assert config == {
        "app": "app.api:app",
        "host": "0.0.0.0",
        "port": 8000,
    }


def test_get_server_config_reads_environment(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9000")

    config = get_server_config()

    assert config["host"] == "127.0.0.1"
    assert config["port"] == 9000


def test_get_server_config_validates_port(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PORT", "not-a-number")

    with pytest.raises(ValueError, match="PORT must be an integer"):
        get_server_config()
