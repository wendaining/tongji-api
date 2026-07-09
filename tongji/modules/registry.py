from __future__ import annotations

from collections.abc import Iterable

from tongji.modules.base import ModuleDefinition


class ModuleRegistry:
    def __init__(self, modules: Iterable[ModuleDefinition]) -> None:
        self._modules: dict[str, ModuleDefinition] = {}
        self._routes: set[tuple[str, str]] = set()
        for module in modules:
            if module.name in self._modules:
                raise ValueError(f"Duplicate module name: {module.name}")
            route_key = (module.method.upper(), module.public_route)
            if route_key in self._routes:
                raise ValueError(f"Duplicate module route: {route_key}")
            self._modules[module.name] = module
            self._routes.add(route_key)

    def get(self, name: str) -> ModuleDefinition:
        try:
            return self._modules[name]
        except KeyError as exc:
            raise KeyError(f"Unknown module: {name}") from exc

    def all(self) -> tuple[ModuleDefinition, ...]:
        return tuple(self._modules.values())

    def metadata(self) -> list[dict[str, object]]:
        return [module.metadata() for module in self.all()]

    def __len__(self) -> int:
        return len(self._modules)


def get_registry() -> ModuleRegistry:
    from tongji.modules.catalog import MODULES

    return ModuleRegistry(MODULES)
