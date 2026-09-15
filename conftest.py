"""
pytest configuration — adds the project root to sys.path so that
tests can import project packages without installing the package.
"""

import sys
import os

# Insert the project root (parent of the tests/ directory) into sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
