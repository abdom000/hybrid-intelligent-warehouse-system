"""Start the backend API and the demo dashboard.

Usage:
    python scripts/run_backend.py [--host 127.0.0.1] [--port 8000]

Then open http://127.0.0.1:8000 in a browser.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import uvicorn  # noqa: E402

from hybrid_warehouse.backend import create_app  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the warehouse backend.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    arguments = parser.parse_args()

    app = create_app(PROJECT_ROOT)
    print("HiveWare — Hybrid Intelligent Warehouse System")
    print(f"Dashboard: http://{arguments.host}:{arguments.port}")
    print(f"API docs:  http://{arguments.host}:{arguments.port}/docs")
    uvicorn.run(app, host=arguments.host, port=arguments.port, log_level="info")


if __name__ == "__main__":
    main()
