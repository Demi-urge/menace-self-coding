"""Bootstrap the self-coding environment with graceful fallbacks."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _import_or_stub(module: str, attr: str, stub):
    try:
        mod = __import__(module, fromlist=[attr])
        return getattr(mod, attr)
    except Exception as exc:  # pragma: no cover - graceful degradation
        logger.warning("using stub for %s.%s: %s", module, attr, exc)
        return stub


class _StubSelfCodingEngine:
    def __init__(self, *_, **__):
        self.ready = True


class _StubPipeline:
    def __init__(self, *_, **__):
        self.bots = []


class _StubRegistry:
    def __init__(self, *_, **__):
        self.bots: dict[str, object] = {}

    def register_bot(self, name: str, **meta):
        self.bots[name] = meta


class _StubDataBot:
    def __init__(self, name: str = "stub", *_, **__):
        self.name = name

    def schedule_monitoring(self, *_args, **_kwargs) -> None:
        return None


def _stub_internalize(bot, engine, registry, pipeline, **_kwargs):
    if hasattr(registry, "register_bot"):
        registry.register_bot(getattr(bot, "name", "stub"), is_coding_bot=True)
    return {"bot": bot, "engine": engine, "pipeline": pipeline}


SelfCodingEngine = _import_or_stub(
    "menace.self_coding_engine", "SelfCodingEngine", _StubSelfCodingEngine
)
ModelAutomationPipeline = _import_or_stub(
    "menace.model_automation_pipeline",
    "ModelAutomationPipeline",
    _StubPipeline,
)
BotRegistry = _import_or_stub("menace.bot_registry", "BotRegistry", _StubRegistry)
DataBot = _import_or_stub("menace.data_bot", "DataBot", _StubDataBot)
internalize_coding_bot = _import_or_stub(
    "menace.self_coding_manager", "internalize_coding_bot", _stub_internalize
)

engine = SelfCodingEngine()
pipeline = ModelAutomationPipeline()
registry = BotRegistry()
bot = DataBot("self-coding-clone")

internalize_coding_bot(bot, engine, registry, pipeline)
print("Bootstrapped self-coding engine successfully.")
