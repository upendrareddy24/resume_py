"""
Compatibility helpers for newer OpenAI Python SDK versions.

`langchain-openai` (<=0.2.x) still attempts to pass a `proxies` keyword to
`openai.OpenAI`. Starting in openai>=1.53 the constructor no longer accepts
that parameter directly. This module patches the client at import time so the
kwarg is still tolerated and routed through an `httpx` client, allowing the
rest of the codebase—and LangChain adapters—to continue working unchanged.
"""

from __future__ import annotations


def _patch_class(cls) -> None:
    if cls is None:
        return
    try:
        import inspect

        sig = inspect.signature(cls.__init__)
    except Exception:
        return
    if "proxies" in sig.parameters:
        return

    original_init = cls.__init__

    def patched_init(self, *args, proxies=None, **kwargs):  # type: ignore[override]
        if proxies:
            try:
                import httpx

                timeout = kwargs.get("timeout", None)
                http_client = httpx.Client(proxies=proxies, timeout=timeout)
                kwargs["http_client"] = http_client
            except Exception:
                pass
        return original_init(self, *args, **kwargs)

    cls.__init__ = patched_init  # type: ignore[assignment]


def patch_openai_client() -> None:
    try:
        import openai
    except Exception:
        return

    candidates: list[object] = []
    for name in ("OpenAI", "AsyncOpenAI", "Client", "AsyncClient", "AzureOpenAI"):
        candidates.append(getattr(openai, name, None))

    # Private client classes (sync + async)
    try:
        from openai import _client  # type: ignore[import]

        candidates.append(getattr(_client, "Client", None))
        candidates.append(getattr(_client, "AsyncClient", None))
    except Exception:
        pass

    # Resource-specific client classes (chat/completions, etc.)
    try:
        from openai.resources import chat  # type: ignore[import]

        candidates.append(getattr(chat.completions, "Client", None))
    except Exception:
        pass

    # Deduplicate while preserving order
    seen: set[object] = set()
    unique_candidates = []
    for cls in candidates:
        if cls and cls not in seen:
            unique_candidates.append(cls)
            seen.add(cls)

    for cls in unique_candidates:
        _patch_class(cls)


patch_openai_client()

