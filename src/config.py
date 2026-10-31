"""Configuration module for Empório da Música AI Assistant."""

from pathlib import Path
import os
from dotenv import load_dotenv

# Base paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs"

# Data file paths
DB_PATH = DATA_DIR / "emporio.db"
POLICY_PDF_PATH = DATA_DIR / "politicas_da_loja.pdf"

# Load environment variables from .env file if present
load_dotenv(ROOT_DIR / ".env")

# LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

# Agent settings
AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.2"))
AGENT_MAX_TURNS = int(os.getenv("AGENT_MAX_TURNS", "6"))
DEBUG_TOOLS = os.getenv("DEBUG_TOOLS", "false").lower() in ("true", "1", "yes")

# Formatting utility
def format_currency_brl(value: float) -> str:
    """Format a float as Brazilian Real (e.g., 2199.0 -> 'R$ 2.199,00')."""
    if value is None:
        return "R$ 0,00"
    formatted = f"{value:,.2f}"
    # Invert commas and dots for Brazilian currency format
    parts = formatted.split(".")
    integer_part = parts[0].replace(",", ".")
    decimal_part = parts[1]
    return f"R$ {integer_part},{decimal_part}"
