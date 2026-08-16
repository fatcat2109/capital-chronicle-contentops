"""Deterministic production control for free-form chapterized V2 films."""

from typing import Any

__all__ = ["FreeformChapterPipeline", "PipelineError"]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(name)
    from .pipeline import FreeformChapterPipeline, PipelineError

    return {
        "FreeformChapterPipeline": FreeformChapterPipeline,
        "PipelineError": PipelineError,
    }[name]
