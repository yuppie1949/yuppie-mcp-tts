"""FNF MCP Server 配置：从环境变量读取并校验"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_ENDPOINT = "cn-hangzhou.fnf.aliyuncs.com"

load_dotenv()


@dataclass
class FNFConfig:
    """运行配置：阿里云凭证 + FNF 服务地址"""

    access_key_id: str
    access_key_secret: str
    endpoint: str = DEFAULT_ENDPOINT

    @classmethod
    def from_env(cls) -> FNFConfig:
        """从环境变量构造配置，缺少必填项时抛 ValueError

        支持两种环境变量命名方式：
        1. 阿里云标准: ALIBABA_CLOUD_ACCESS_KEY_ID / ALIBABA_CLOUD_ACCESS_KEY_SECRET
        2. 项目专用:   FNF_ACCESS_KEY_ID / FNF_ACCESS_KEY_SECRET
        项目专用优先。
        """
        access_key_id = (
            os.environ.get("FNF_ACCESS_KEY_ID")
            or os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID")
            or ""
        ).strip()
        access_key_secret = (
            os.environ.get("FNF_ACCESS_KEY_SECRET")
            or os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
            or ""
        ).strip()
        endpoint = os.environ.get("FNF_ENDPOINT", DEFAULT_ENDPOINT).strip()

        if not access_key_id:
            raise ValueError("缺少必填环境变量 FNF_ACCESS_KEY_ID 或 ALIBABA_CLOUD_ACCESS_KEY_ID")
        if not access_key_secret:
            raise ValueError(
                "缺少必填环境变量 FNF_ACCESS_KEY_SECRET 或 ALIBABA_CLOUD_ACCESS_KEY_SECRET"
            )

        return cls(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            endpoint=endpoint,
        )
