# Environment detection and setup
import sys
from pathlib import Path

# Always add the directory containing this utils package to Python path
# This ensures utils can be imported regardless of the current working directory
utils_dir = Path(__file__).parent.parent  # Go up one level from utils/__init__.py
if str(utils_dir) not in sys.path:
    sys.path.insert(0, str(utils_dir))

# Import the main classes
from .download_utils import GoldenCopyDownload
from .gleif_api_utils import GLEIFAPI
from .visualization_utils import Visualizations
from .codelist_utils import Codelists

__all__ = [
    "GoldenCopyDownload",
    "GLEIFAPI",
    "Visualizations",
    "Codelists",
]
