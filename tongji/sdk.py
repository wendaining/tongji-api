from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient
from tongji.modules.registry import ModuleRegistry, get_registry


class TongjiClient:
    """Python SDK facade over the same modules exposed by the HTTP server."""

    def __init__(
        self,
        raw_client: RawOneClient,
        *,
        registry: ModuleRegistry | None = None,
    ) -> None:
        self.raw_client = raw_client
        self.registry = registry or get_registry()

    async def call(self, module_name: str, params: dict[str, Any] | None = None) -> Any:
        module = self.registry.get(module_name)
        request = module.request_model.model_validate(params or {})
        return await module.execute(self.raw_client, request)

    def modules(self) -> list[dict[str, object]]:
        return self.registry.metadata()
