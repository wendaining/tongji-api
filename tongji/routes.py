from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError

from tongji.modules.base import ModuleDefinition
from tongji.modules.registry import ModuleRegistry


def _parameter_docs(module: ModuleDefinition) -> list[dict[str, Any]]:
    schema = module.request_model.model_json_schema(by_alias=True)
    required = set(schema.get("required", []))
    path_names = {
        part.split("}", 1)[0] for part in module.public_route.split("{")[1:] if "}" in part
    }
    parameters: list[dict[str, Any]] = []
    for name, field_schema in schema.get("properties", {}).items():
        python_name = next(
            (
                field_name
                for field_name, field in module.request_model.model_fields.items()
                if (field.alias or field_name) == name
            ),
            name,
        )
        location = "path" if python_name in path_names or name in path_names else "query"
        parameters.append(
            {
                "name": python_name if location == "path" else name,
                "in": location,
                "required": True if location == "path" else name in required,
                "schema": field_schema,
            }
        )
    return parameters


async def _request_values(request: Request) -> dict[str, Any]:
    values: dict[str, Any] = dict(request.query_params)
    values.update(request.path_params)
    if request.method not in {"GET", "HEAD"}:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            if isinstance(body, Mapping):
                values.update(body)
        elif "application/x-www-form-urlencoded" in content_type:
            parsed = parse_qs((await request.body()).decode(), keep_blank_values=True)
            values.update({key: value[-1] for key, value in parsed.items()})
    return values


def _endpoint(module: ModuleDefinition):
    async def endpoint(request: Request) -> Any:
        values = await _request_values(request)
        try:
            payload: BaseModel = module.request_model.model_validate(values)
        except ValidationError as exc:
            raise RequestValidationError(exc.errors(), body=values) from exc
        return await module.execute(request.app.state.raw_client, payload)

    endpoint.__name__ = module.name
    endpoint.__doc__ = module.description
    return endpoint


def build_raw_router(registry: ModuleRegistry) -> APIRouter:
    router = APIRouter(tags=["raw-api"])
    modules = sorted(
        registry.all(),
        key=lambda module: ("{" in module.public_route, module.public_route),
    )
    for module in modules:
        router.add_api_route(
            module.public_route,
            _endpoint(module),
            methods=[module.method],
            name=module.name,
            summary=module.summary,
            description=module.description,
            tags=list(module.tags),
            response_model=module.response_model,
            response_model_by_alias=True,
            openapi_extra={"parameters": _parameter_docs(module)},
        )
    return router
