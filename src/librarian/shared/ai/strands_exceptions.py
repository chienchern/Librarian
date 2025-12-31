"""Strands-specific exception handling utilities."""

import logging
from strands.types.exceptions import StructuredOutputException

logger = logging.getLogger("librarian")


def handle_structured_output_error(e: StructuredOutputException, context: str) -> None:
    """Handle structured output exceptions with consistent logging."""
    logger.error(f"Structured output failed in {context}: {e}")


def safe_structured_output(agent_call, fallback_value=None, context: str = "unknown"):
    """Safely execute agent call with structured output, returning fallback on error."""
    try:
        return agent_call()
    except StructuredOutputException as e:
        handle_structured_output_error(e, context)
        return fallback_value
    except Exception as e:
        logger.error(f"Agent call failed in {context}: {e}")
        return fallback_value