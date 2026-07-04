from __future__ import annotations

import os

import uvicorn


def get_server_config() -> dict[str, object]:
    host = os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0"
    port_raw = os.getenv("PORT", "8000").strip() or "8000"

    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ValueError("PORT must be an integer.") from exc

    if port <= 0:
        raise ValueError("PORT must be greater than 0.")

    return {
        "app": "app.api:app",
        "host": host,
        "port": port,
    }


def main() -> None:
    uvicorn.run(**get_server_config())


if __name__ == "__main__":
    main()
