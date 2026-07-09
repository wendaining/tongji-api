from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any, TypeAlias

from pydantic import BaseModel, ConfigDict, RootModel, create_model

from tongji.core.client import RawOneClient

RawPayload: TypeAlias = dict[str, Any] | list[Any] | str | int | float | bool | None
ModuleExecutor: TypeAlias = Callable[[RawOneClient, BaseModel], Awaitable[RawPayload]]


class ModuleRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


def create_request_model(
    name: str,
    fields: Mapping[str, tuple[Any, Any]],
) -> type[ModuleRequest]:
    return create_model(  # type: ignore[call-overload]
        name,
        __base__=ModuleRequest,
        **dict(fields),
    )


def create_raw_response_model(name: str) -> type[RootModel[RawPayload]]:
    class RawResponse(RootModel[RawPayload]):
        pass

    RawResponse.__name__ = name
    RawResponse.__qualname__ = name
    return RawResponse


@dataclass(frozen=True, slots=True)
class ModuleDefinition:
    name: str
    route: str
    method: str
    summary: str
    description: str
    tags: tuple[str, ...]
    request_model: type[ModuleRequest]
    response_model: type[RootModel[RawPayload]]
    execute: ModuleExecutor

    @property
    def public_route(self) -> str:
        return f"/api{self.route}"

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "method": self.method,
            "route": self.public_route,
            "summary": self.summary,
            "description": self.description,
            "tags": list(self.tags),
            "request_schema": self.request_model.model_json_schema(by_alias=True),
            "response_schema": self.response_model.model_json_schema(),
        }
