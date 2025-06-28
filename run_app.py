import os
import sys
from src.prototype.main import main

if __name__ == "__main__":
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    with open("output.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        sys.stderr = f
        main()