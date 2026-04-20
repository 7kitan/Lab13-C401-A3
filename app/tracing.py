from __future__ import annotations

import os
from typing import Any
from dotenv import load_dotenv

# Load env vars before importing langfuse to ensure it picks up host/keys
load_dotenv()

try:
    # In Langfuse 3.x, some distributions have observe at the top level
    from langfuse import observe, langfuse_context
    _tracing_mode = "REAL (Top-level)"
except ImportError:
    try:
        # Fallback to the newer pattern found in version 3.2.x
        from langfuse import observe
        
        class _ContextProxy:
            def update_current_trace(self, **kwargs: Any) -> None:
                try:
                    from langfuse import get_client
                    get_client().update_current_trace(**kwargs)
                except Exception:
                    pass

            def update_current_observation(self, **kwargs: Any) -> None:
                try:
                    from langfuse import get_client
                    # In SDK 3.2.x, we use update_current_span for generic observations
                    get_client().update_current_span(**kwargs)
                except Exception:
                    pass

            def get_current_trace_id(self) -> str:
                try:
                    from langfuse import get_client
                    return get_client().get_current_trace_id()
                except Exception:
                    return "unknown-trace"

        langfuse_context = _ContextProxy()
        _tracing_mode = "REAL (Proxy-3.2.x)"
    except ImportError:
        _tracing_mode = "DUMMY (Fallback)"
        def observe(*args: Any, **kwargs: Any):
            def decorator(func):
                return func
            return decorator

        class _DummyContext:
            def update_current_trace(self, **kwargs: Any) -> None:
                pass
            def update_current_observation(self, **kwargs: Any) -> None:
                pass
            def get_current_trace_id(self) -> str:
                return "dummy-trace-id"

        langfuse_context = _DummyContext()

print(f"[*] Langfuse tracing: {_tracing_mode} | Host: {os.getenv('LANGFUSE_HOST')}")


def tracing_enabled() -> bool:
    """Check if tracing is configured with both keys and a valid host."""
    has_keys = bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
    has_host = bool(os.getenv("LANGFUSE_HOST"))
    return has_keys and has_host
