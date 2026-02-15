import json
from typing import Any, Dict, List

from utils.database import MockDatabase


def get_fixture_data(path: str, fixture_name: str) -> List[Dict[str, Any]]:
    with open(f"{path}/fixtures/{fixture_name}.json") as fixtures:
        return json.load(fixtures)


async def load_mock_data(mock_data: List[Dict[str, Any]], mock_db: MockDatabase) -> None:
    for data in mock_data:
        await mock_db.load_rows(data["class"], data["json"])
