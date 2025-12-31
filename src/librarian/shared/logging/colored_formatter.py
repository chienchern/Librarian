import logging
import colorama
from colorama import Fore, Back, Style

colorama.init()


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and separators."""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        reset = Style.RESET_ALL
        
        # Add separators for major steps
        if hasattr(record, 'step'):
            separator = f"\n{Fore.BLUE}{'='*60}{Style.RESET_ALL}"
            record.msg = f"{separator}\n{record.msg}\n{Fore.BLUE}{'='*60}{Style.RESET_ALL}"
        elif hasattr(record, 'query'):
            record.msg = f"{Fore.MAGENTA}QUERY:{Style.RESET_ALL} {record.msg}"
        elif hasattr(record, 'response'):
            record.msg = f"{Fore.CYAN}RESPONSE:{Style.RESET_ALL} {record.msg}"
        
        return f"{color}{record.levelname}:{reset} {record.msg}"


def setup_logging():
    """Setup logging with colored formatter."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler()]
    )

    # Apply colored formatter to our logger
    logger = logging.getLogger("librarian")
    logger.setLevel(logging.INFO)
    
    # Remove any existing handlers to avoid duplication
    logger.handlers.clear()
    
    # Create a new handler with our colored formatter
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter())
    logger.addHandler(handler)
    
    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False

    # Set httpx to WARNING level to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)