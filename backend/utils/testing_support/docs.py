from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
OPERATIONS_DOCS_DIR = BACKEND_DIR / "docs" / "operations"
AUTHORIZATION_MATRIX_PATH = OPERATIONS_DOCS_DIR / "authorization_matrix.md"
API_ENDPOINTS_PATH = OPERATIONS_DOCS_DIR / "api_endpoints.md"
