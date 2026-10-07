"""The Mines in the Dataset (sftcheck).

Chinese-first pre-flight structural auditing for SFT fine-tuning datasets
(alpaca / sharegpt / OpenAI dialects). Deterministic, character-level and
row-level evidence; it does not judge sample quality or promise training
success.
"""
from .inspector import inspect_file, inspect_path
from .model import (
    SEVERITY_ERROR,
    SEVERITY_INFO,
    SEVERITY_WARN,
    Issue,
    Report,
    SPEC_VERSION,
)

__all__ = [
    "inspect_file",
    "inspect_path",
    "Issue",
    "Report",
    "SPEC_VERSION",
    "SEVERITY_ERROR",
    "SEVERITY_WARN",
    "SEVERITY_INFO",
    "__version__",
]
__version__ = "0.1.0a1"
