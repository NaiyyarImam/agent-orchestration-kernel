"""Research backend interface for the JARVIS Kernel.

Defines the port that every research/search backend must implement.
Remote search APIs (Tavily, Exa, Perplexity), MCP servers, local
indexes, and hybrid search engines all live behind this interface.

The Kernel (ExecutiveEngine -> CapabilityAdapterManager ->
ResearchAdapter) depends only on this interface. Concrete backends
are constructed exclusively by the composition root (Bootstrap) and
injected into the ResearchAdapter; neither the Kernel nor the adapter
ever instantiates a backend itself. The Kernel never knows which
backend is in use, how the search is performed, or whether the backend
is local or remote.

Optional members: ``search`` is the only required member. Backends may
additionally advertise lifecycle hooks (``initialize``, ``shutdown``,
``health_check``) and metadata (``name``, ``description``,
``capabilities``); the ResearchAdapter discovers them defensively, so
minimal backends that only implement ``search`` work exactly as before.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ResearchResult:
    """A single research finding returned by a ResearchBackend.

    Backends may alternatively return plain dictionaries with the same
    keys; the ResearchAdapter accepts both forms.
    """

    title: str
    snippet: str
    url: str | None = None
    source: str | None = None


@runtime_checkable
class ResearchBackend(Protocol):
    """Port implemented by every research/search backend.

    The runtime-checked surface is exactly ``search``; backends are
    structurally compatible by implementing that single method.

    Optional lifecycle hooks (invoked by the ResearchAdapter when
    present; minimal backends may omit them entirely):

        initialize()      async; prepare backend resources.
        shutdown()        async; release backend resources.
        health_check()    async; return backend health as bool.

    Optional metadata attributes (describe the backend for tooling;
    never required at runtime):

        name             str
        description      str
        capabilities     tuple[str, ...] or list[str]

    Backends are constructed exclusively by the composition root
    (Bootstrap) and injected into the ResearchAdapter; the adapter
    never instantiates a backend itself.
    """

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        context: dict[str, Any] | None = None,
    ) -> Iterable[ResearchResult] | None:
        """Search for findings matching ``query``.

        Returns an iterable of ResearchResult (or dict) findings. An
        empty iterable or ``None`` is a valid, empty response.
        """
