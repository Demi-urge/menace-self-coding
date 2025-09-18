"""Provide a module level GPT memory manager instance."""

from __future__ import annotations

from gpt_memory_interface import GPTMemoryInterface

GPT_MEMORY_MANAGER = GPTMemoryInterface()

__all__ = ["GPT_MEMORY_MANAGER"]

