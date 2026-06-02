"""
Help module — re-exports the help handler registration.
This module exists as a standalone for clarity.
"""

from modules.owner import register as register_owner_help

# Help is part of owner.py (the .help command lives there).
# This file re-exports for module discovery purposes.
__all__ = ["register_owner_help"]
