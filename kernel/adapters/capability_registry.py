from kernel.interfaces.capability_registry import CapabilityRegistry, CapabilityMetadata


class InMemoryCapabilityRegistry(CapabilityRegistry):
    """In-memory implementation of the CapabilityRegistry interface."""
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._capability_metadata: dict[str, CapabilityMetadata] = {}

    async def register(self, capability: CapabilityMetadata) -> None:
        self._capability_metadata[capability.name] = capability

    async def unregister(self, name: str) -> bool:
        if name in self._capability_metadata:
            del self._capability_metadata[name]
            return True
        return False

    async def get(self, name: str) -> CapabilityMetadata:
        if name not in self._capability_metadata:
            raise KeyError(name)
        return self._capability_metadata[name]

    async def list_capabilities(self) -> list[CapabilityMetadata]:
        return list(self._capability_metadata.values())

    async def exists(self, name: str) -> bool:
        return name in self._capability_metadata

    async def search(self, tag: str) -> list[CapabilityMetadata]:
        return [cap for cap in self._capability_metadata.values() if tag in cap.tags]

    async def health_check(self) -> bool:
        return True
