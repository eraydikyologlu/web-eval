"""
Modern Web Test Automation Framework

LLM-yerleşik, agent-tabanlı ve YAML-driven web test otomasyon framework'ü.
"""

__version__ = "1.0.0"
__author__ = "AI Test Automation Team"

from .agents import CrewManager
from .models import Scenario, Step
from .utils import Config, setup_logging, YamlLoader

__all__ = [
    "CrewManager",
    "Scenario", 
    "Step",
    "Config",
    "setup_logging",
    "YamlLoader"
] 