"""Per-language adapters. New languages plug in here."""

from codeintel_engine.adapters.base import LanguageAdapter, registry
from codeintel_engine.adapters.python import PythonAdapter
from codeintel_engine.adapters.typescript import TypeScriptAdapter

registry.register(PythonAdapter())
registry.register(TypeScriptAdapter())

__all__ = ["LanguageAdapter", "PythonAdapter", "TypeScriptAdapter", "registry"]
