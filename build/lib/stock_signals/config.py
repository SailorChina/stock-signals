# -*- coding: utf-8 -*-
"""Default configuration"""
from dataclasses import dataclass


@dataclass
class Config:
    host: str = "127.0.0.1"
    port: int = 11111
    default_kline_num: int = 300
    trend_weight: float = 0.30
    momentum_weight: float = 0.25
    volume_weight: float = 0.20
    volatility_weight: float = 0.15
    capital_weight: float = 0.10
    stop_loss_pct: float = 0.05
    risk_reward_min: float = 2.0
    cache_dir: str = ""
    cache_ttl: int = 300
    max_retries: int = 3
    retry_delay: float = 1.0
    log_level: str = "INFO"
    log_file: str = ""


config = Config()


def load_config(path=None):
    import json
    if path is None:
        import os
        for p in [
            os.path.join(os.path.expanduser("~"), ".tech-signal-FUTU-skill", "config.json"),
            os.path.join(os.getcwd(), "config.json"),
        ]:
            if os.path.exists(p):
                path = p
                break
    if path is None or not os.path.exists(path):
        return config
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for key, val in data.items():
        if hasattr(config, key):
            setattr(config, key, val)
    return config
