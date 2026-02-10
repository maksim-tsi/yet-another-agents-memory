import sys
from pathlib import Path

# Resolve path collision between local 'datasets' package and installed 'datasets' (HuggingFace) library
# caused by 'transformers' dependency. We force the project root to be first in sys.path.
root_dir = str(Path(__file__).parent.parent.absolute())

print(f"DEBUG: Inserting root_dir to sys.path[0]: {root_dir}")

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
elif sys.path[0] != root_dir:
    sys.path.remove(root_dir)
    sys.path.insert(0, root_dir)
