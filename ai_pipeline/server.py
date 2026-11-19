"""Backwards-compatible entry point.

The application now lives in ``ai_pipeline.app``. Keep this module so existing
commands such as ``uvicorn ai_pipeline.server:app`` continue to work.
"""

from .app import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("ai_pipeline.server:app", host="127.0.0.1", port=8000, reload=True)
