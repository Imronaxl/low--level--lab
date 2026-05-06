"""Микрокод для CISC процессора."""

from .microcode import MICROCODE, MicroOp, get_microcode

__all__ = ["MicroOp", "MICROCODE", "get_microcode"]
