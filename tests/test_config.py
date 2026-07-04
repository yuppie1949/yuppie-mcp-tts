"""FNFConfig 环境变量读取与校验测试"""

import pytest

from yuppie_mcp_fnf.utils.config import DEFAULT_ENDPOINT, FNFConfig


def test_from_env_requires_key_id(monkeypatch):
    monkeypatch.setenv("FNF_ACCESS_KEY_ID", "")
    monkeypatch.setenv("FNF_ACCESS_KEY_SECRET", "secret")
    monkeypatch.delenv("ALIBABA_CLOUD_ACCESS_KEY_ID", raising=False)
    with pytest.raises(ValueError, match="FNF_ACCESS_KEY_ID|ALIBABA_CLOUD_ACCESS_KEY_ID"):
        FNFConfig.from_env()


def test_from_env_requires_key_secret(monkeypatch):
    monkeypatch.setenv("FNF_ACCESS_KEY_ID", "id")
    monkeypatch.setenv("FNF_ACCESS_KEY_SECRET", "")
    monkeypatch.delenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", raising=False)
    with pytest.raises(ValueError, match="FNF_ACCESS_KEY_SECRET|ALIBABA_CLOUD_ACCESS_KEY_SECRET"):
        FNFConfig.from_env()


def test_from_env_reads_project_specific_vars(monkeypatch):
    monkeypatch.setenv("FNF_ACCESS_KEY_ID", "fnf_id")
    monkeypatch.setenv("FNF_ACCESS_KEY_SECRET", "fnf_secret")
    monkeypatch.delenv("ALIBABA_CLOUD_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", raising=False)
    monkeypatch.delenv("FNF_ENDPOINT", raising=False)
    cfg = FNFConfig.from_env()
    assert cfg.access_key_id == "fnf_id"
    assert cfg.access_key_secret == "fnf_secret"
    assert cfg.endpoint == DEFAULT_ENDPOINT


def test_from_env_falls_back_to_alibaba_standard_vars(monkeypatch):
    monkeypatch.delenv("FNF_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("FNF_ACCESS_KEY_SECRET", raising=False)
    monkeypatch.setenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "ali_id")
    monkeypatch.setenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "ali_secret")
    cfg = FNFConfig.from_env()
    assert cfg.access_key_id == "ali_id"
    assert cfg.access_key_secret == "ali_secret"


def test_project_specific_takes_priority(monkeypatch):
    monkeypatch.setenv("FNF_ACCESS_KEY_ID", "fnf_id")
    monkeypatch.setenv("FNF_ACCESS_KEY_SECRET", "fnf_secret")
    monkeypatch.setenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "ali_id")
    monkeypatch.setenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "ali_secret")
    cfg = FNFConfig.from_env()
    assert cfg.access_key_id == "fnf_id"
    assert cfg.access_key_secret == "fnf_secret"


def test_from_env_accepts_custom_endpoint(monkeypatch):
    monkeypatch.setenv("FNF_ACCESS_KEY_ID", "id")
    monkeypatch.setenv("FNF_ACCESS_KEY_SECRET", "secret")
    monkeypatch.setenv("FNF_ENDPOINT", "ap-southeast-1.fnf.aliyuncs.com")
    cfg = FNFConfig.from_env()
    assert cfg.endpoint == "ap-southeast-1.fnf.aliyuncs.com"


def test_from_env_strips_whitespace(monkeypatch):
    monkeypatch.setenv("FNF_ACCESS_KEY_ID", "  id  ")
    monkeypatch.setenv("FNF_ACCESS_KEY_SECRET", "  secret  ")
    monkeypatch.delenv("ALIBABA_CLOUD_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", raising=False)
    cfg = FNFConfig.from_env()
    assert cfg.access_key_id == "id"
    assert cfg.access_key_secret == "secret"
