"""Allow `python -m metro_router`."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
