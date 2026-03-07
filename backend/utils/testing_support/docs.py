from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
DOCS_DIR = BACKEND_DIR / "docs"
OPERATIONS_DOCS_DIR = DOCS_DIR / "operations"
TEMPLATES_DOCS_DIR = DOCS_DIR / "templates"

BACKEND_PLAYBOOK_PATH = DOCS_DIR / "backend_playbook.md"
AUTHORIZATION_MATRIX_PATH = OPERATIONS_DOCS_DIR / "authorization_matrix.md"
API_ENDPOINTS_PATH = OPERATIONS_DOCS_DIR / "api_endpoints.md"
FEATURE_REQUEST_TEMPLATE_PATH = TEMPLATES_DOCS_DIR / "feature_request.md"
INTEGRATION_REQUEST_TEMPLATE_PATH = TEMPLATES_DOCS_DIR / "integration_request.md"
CODE_CHANGE_REQUEST_TEMPLATE_PATH = TEMPLATES_DOCS_DIR / "code_change_request.md"
