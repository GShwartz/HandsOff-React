# Modules/__init__.py

from.startup import Startup
from .backend import Backend
from .commands import Commands
from .controller import Controller
from .logger import init_logger
from .operations import Operations
from .screenshot import Screenshot
from .server import Server
from .utils import Handlers

from .sysinfo import Sysinfo
from .tasks import Tasks

# Package version
__version__ = "1.0.0"

# Exposed modules
__all__ = [
    "Startup",
    "Backend",
    "Commands",
    "Controller",
    "init_logger",
    "Operations",
    "Screenshot",
    "Server",
    "Handlers",
    "Sysinfo",
    "Tasks"
]
