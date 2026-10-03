"""Pytest configuration.

Make the ``pycrc`` source tree importable when the tests are run without an
editable install (``pip install -e .``).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
