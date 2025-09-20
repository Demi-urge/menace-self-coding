"""Alias to :mod:`menace.self_improvement` for legacy imports."""

from __future__ import annotations

import sys
from importlib import import_module

_pkg = import_module("menace.self_improvement")
sys.modules[__name__] = _pkg
