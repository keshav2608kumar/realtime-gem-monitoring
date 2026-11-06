# empty conftest
import sys
import os

# Allow imports from backend/app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
