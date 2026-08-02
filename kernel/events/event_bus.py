"""Backward-compatible access to the in-memory EventBus implementation."""

from kernel.events.in_memory_event_bus import InMemoryEventBus

# Historical import path retained for callers that instantiated EventBus
# directly. New dependencies must target kernel.interfaces.event_bus.EventBus.
EventBus = InMemoryEventBus

__all__ = ["EventBus"]
