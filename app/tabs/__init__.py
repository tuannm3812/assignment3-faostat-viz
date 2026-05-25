"""Dashboard tab package exports."""

from __future__ import annotations

from app.tabs.context import slide_context
from app.tabs.evidence import appendix
from app.tabs.executive import executive_brief
from app.tabs.producer import slide_producer_signal
from app.tabs.vulnerability import slide_vulnerability
from app.tabs.what_if import slide_what_if

__all__ = [
    "appendix",
    "executive_brief",
    "slide_context",
    "slide_producer_signal",
    "slide_vulnerability",
    "slide_what_if",
]
