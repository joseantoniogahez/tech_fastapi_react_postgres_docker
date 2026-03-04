import json
from typing import Any

from utils.testing_support.database import MockDatabase


def get_fixture_data(path: str, fixture_name: str) -> list[dict[str, Any]]:
    with open(f"{path}/fixtures/{fixture_name}.json", encoding="utf-8") as fixtures:
        return json.load(fixtures)


async def load_mock_data(mock_data: list[dict[str, Any]], mock_db: MockDatabase) -> None:
    for data in mock_data:
        await mock_db.load_rows(data["class"], data["json"])
