from menace.self_coding_engine import SelfCodingEngine
from menace.model_automation_pipeline import ModelAutomationPipeline
from menace.bot_registry import BotRegistry
from menace.data_bot import DataBot
from menace.internalize_coding_bot import internalize_coding_bot

engine = SelfCodingEngine()
pipeline = ModelAutomationPipeline()
registry = BotRegistry()
bot = DataBot("self-coding-clone")

internalize_coding_bot(bot, engine, registry, pipeline)
print("Bootstrapped self-coding engine successfully.")
