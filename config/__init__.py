"""Simplified configuration objects used across the sandbox."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set


@dataclass
class ContextBuilderConfig:
    ranking_weight: float = 1.0
    roi_weight: float = 1.0
    recency_weight: float = 1.0
    safety_weight: float = 1.0
    max_tokens: int = 800
    regret_penalty: float = 0.0
    alignment_penalty: float = 0.0
    alert_penalty: float = 0.0
    risk_penalty: float = 0.0
    roi_tag_penalties: Dict[str, float] = field(default_factory=dict)
    enhancement_weight: float = 0.0
    max_alignment_severity: float = 1.0
    max_alerts: int = 5
    license_denylist: Set[str] = field(default_factory=set)
    precise_token_count: bool = True
    max_diff_lines: int = 200
    similarity_metric: str = "cosine"
    embedding_check_interval: int = 0
    prompt_score_weight: float = 1.0
    prompt_max_tokens: int = 800


@dataclass
class LoggingSettings:
    verbosity: str = "INFO"


@dataclass
class _Config:
    logging: LoggingSettings = field(default_factory=LoggingSettings)


_GLOBAL_CONFIG = _Config()


def get_config() -> _Config:  # pragma: no cover - trivial
    return _GLOBAL_CONFIG


__all__ = ["ContextBuilderConfig", "get_config"]
config/roi_tag_sentiment.yaml
New
+8
-0

# Default ROI tag sentiment used when the enterprise configuration is absent.
# Positive values increase ranking weights while negative values decrease them.
SUCCESS: 1.0
HIGH_ROI: 1.0
LOW_ROI: -1.0
BUG_INTRODUCED: -1.0
NEEDS_REVIEW: -1.0
BLOCKED: -1.0
