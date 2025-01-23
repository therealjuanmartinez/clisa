import tomli
import sys

try:
    with open("/home/juan/gpt-cli/pyproject.toml", "rb") as f:
        tomli.load(f)
    print("pyproject.toml is valid.")
except Exception as e:
    print(f"Error in pyproject.toml: {e}")
    sys.exit(1)
