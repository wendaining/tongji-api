from __future__ import annotations

from tongji.modules import get_registry
from tongji.server import create_app


def test_registry_contains_45_unique_modules():
    registry = get_registry()

    assert len(registry) == 45
    assert len({module.name for module in registry.all()}) == 45
    assert len({(module.method, module.public_route) for module in registry.all()}) == 45


def test_every_module_has_models_and_documentation():
    for module in get_registry().all():
        assert module.summary
        assert module.description
        assert module.request_model.model_json_schema()
        assert module.response_model.model_json_schema()


def test_openapi_documents_every_raw_module():
    schema = create_app().openapi()
    raw_operations = []
    for path, path_item in schema["paths"].items():
        if not path.startswith("/api/"):
            continue
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            raw_operations.append(operation)
            assert operation["summary"]
            assert operation["description"]
            response = operation["responses"]["200"]
            assert response["content"]["application/json"]["schema"]

    assert len(raw_operations) == 45


def test_openapi_exposes_14_agent_tools():
    paths = create_app().openapi()["paths"]
    tool_paths = [path for path in paths if path.startswith("/tools/tongji/")]
    assert len(tool_paths) == 14


def test_static_notice_route_precedes_notice_id_route():
    paths = list(create_app().openapi()["paths"])
    assert paths.index("/api/notices/unread-count") < paths.index("/api/notices/{notice_id}")
