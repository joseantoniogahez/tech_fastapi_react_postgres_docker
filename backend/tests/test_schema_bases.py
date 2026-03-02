import unittest

from pydantic import BaseModel

from app.schemas.api.base import ApiSchema
from app.schemas.application.base import ApplicationSchema


class _ApiPayload(BaseModel):
    value: str


class _ApplicationPayload(BaseModel):
    value: str


class _ApiResult(ApiSchema):
    value: str


class _ApplicationResult(ApplicationSchema):
    value: str


class ApplicationSchemaTests(unittest.TestCase):
    def test_from_api_accepts_pydantic_payload(self) -> None:
        result = _ApplicationResult.from_api(_ApiPayload(value="test"))

        self.assertIsInstance(result, _ApplicationResult)
        self.assertEqual(result.value, "test")

    def test_from_api_accepts_dict_payload(self) -> None:
        result = _ApplicationResult.from_api({"value": "test"})

        self.assertIsInstance(result, _ApplicationResult)
        self.assertEqual(result.value, "test")


class ApiSchemaTests(unittest.TestCase):
    def test_from_application_accepts_pydantic_payload(self) -> None:
        result = _ApiResult.from_application(_ApplicationPayload(value="test"))

        self.assertIsInstance(result, _ApiResult)
        self.assertEqual(result.value, "test")

    def test_from_application_accepts_dict_payload(self) -> None:
        result = _ApiResult.from_application({"value": "test"})

        self.assertIsInstance(result, _ApiResult)
        self.assertEqual(result.value, "test")
