
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add the project folder to Python's import path.
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from gui.app import launch_app

if __name__ == "__main__":
    launch_app()
