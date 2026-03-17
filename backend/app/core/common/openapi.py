from typing import Any

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_EXAMPLE = "req-example-1234"
VALIDATION_ERROR_RESPONSE_KEY = "422"

ERROR_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["detail", "status", "code", "request_id"],
    "properties": {
        "detail": {"type": "string", "description": "Human-readable error message."},
        "status": {"type": "integer", "description": "HTTP status code."},
        "code": {"type": "string", "description": "Machine-readable domain error code."},
        "request_id": {
            "type": "string",
            "description": "Request correlation identifier echoed in the response header.",
            "example": REQUEST_ID_EXAMPLE,
        },
        "meta": {"description": "Optional structured error metadata."},
    },
}

REQUEST_ID_RESPONSE_HEADER: dict[str, Any] = {
    REQUEST_ID_HEADER: {
        "description": "Request correlation identifier for diagnostics and support.",
        "schema": {"type": "string", "example": REQUEST_ID_EXAMPLE},
    }
}

WWW_AUTHENTICATE_HEADER: dict[str, Any] = {
    "WWW-Authenticate": {
        "description": "Bearer authentication challenge.",
        "schema": {"type": "string", "example": "Bearer"},
    }
}

INTERNAL_ERROR_EXAMPLE: dict[str, Any] = {
    "detail": "Internal server error",
    "status": 500,
    "code": "internal_error",
}


def _with_request_id(example: dict[str, Any]) -> dict[str, Any]:
    return {
        **example,
        "request_id": example.get("request_id", REQUEST_ID_EXAMPLE),
    }


def _contains_component_ref(node: Any, ref: str) -> bool:
    if isinstance(node, dict):
        if node.get("$ref") == ref:
            return True
        return any(_contains_component_ref(value, ref) for value in node.values())
    if isinstance(node, list):
        return any(_contains_component_ref(item, ref) for item in node)
    return False


def _remove_unreferenced_schema_component(openapi_schema: dict[str, Any], schema_name: str) -> None:
    components = openapi_schema.get("components")
    if not isinstance(components, dict):
        return

    schemas = components.get("schemas")
    if not isinstance(schemas, dict) or schema_name not in schemas:
        return

    ref = f"#/components/schemas/{schema_name}"
    remaining_schema = {
        **openapi_schema,
        "components": {
            **components,
            "schemas": {name: value for name, value in schemas.items() if name != schema_name},
        },
    }
    if not _contains_component_ref(remaining_schema, ref):
        schemas.pop(schema_name, None)


def build_error_response(
    *,
    description: str,
    example: dict[str, Any],
    include_www_authenticate: bool = False,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "description": description,
        "content": {
            "application/json": {
                "schema": ERROR_RESPONSE_SCHEMA,
                "example": _with_request_id(example),
            }
        },
        "headers": dict(REQUEST_ID_RESPONSE_HEADER),
    }
    if include_www_authenticate:
        response["headers"].update(WWW_AUTHENTICATE_HEADER)
    return response


def normalize_generated_openapi_schema(openapi_schema: dict[str, Any]) -> dict[str, Any]:
    for path_item in openapi_schema.get("paths", {}).values():
        if not isinstance(path_item, dict):
            continue

        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue

            responses = operation.get("responses")
            if isinstance(responses, dict):
                responses.pop(VALIDATION_ERROR_RESPONSE_KEY, None)
                responses.pop(422, None)

    _remove_unreferenced_schema_component(openapi_schema, "HTTPValidationError")
    _remove_unreferenced_schema_component(openapi_schema, "ValidationError")
    return openapi_schema
