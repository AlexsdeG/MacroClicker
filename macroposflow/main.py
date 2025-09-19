"""
Main entry point for MacroPosFlow.

This module wires together the CLI interface and core functionality.
"""

import sys
import logging
from typing import Optional

from .cli.consolemenu_cli import ConsoleMenuCLI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main entry point for MacroPosFlow.
    
    This function initializes the CLI interface and starts the application.
    """
    try:
        logger.info("Starting MacroPosFlow")
        
        # Initialize the CLI interface
        cli = ConsoleMenuCLI()
        
        # Start the CLI menu loop
        cli.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()