import asyncio

import pytest

from app.repositories.uow import UnitOfWork
from utils.testing_support.repositories import build_session_mock


def test_unit_of_work_commits_when_scope_succeeds() -> None:
    session = build_session_mock()
    unit_of_work = UnitOfWork(session=session)

    async def run_test() -> None:
        async with unit_of_work:
            pass

        session.commit.assert_awaited_once()
        session.rollback.assert_not_awaited()

    asyncio.run(run_test())


def test_unit_of_work_rolls_back_when_scope_fails() -> None:
    session = build_session_mock()
    unit_of_work = UnitOfWork(session=session)

    async def run_test() -> None:
        with pytest.raises(RuntimeError):
            async with unit_of_work:
                raise RuntimeError("boom")

        session.rollback.assert_awaited_once()
        session.commit.assert_not_awaited()

    asyncio.run(run_test())


def test_unit_of_work_commits_once_for_nested_successful_scopes() -> None:
    session = build_session_mock()
    unit_of_work = UnitOfWork(session=session)

    async def run_test() -> None:
        async with unit_of_work:
            async with unit_of_work:
                pass

        session.commit.assert_awaited_once()
        session.rollback.assert_not_awaited()

    asyncio.run(run_test())


def test_unit_of_work_skips_commit_after_inner_scope_failure_even_if_handled() -> None:
    session = build_session_mock()
    unit_of_work = UnitOfWork(session=session)

    async def run_test() -> None:
        async with unit_of_work:
            try:
                async with unit_of_work:
                    raise ValueError("inner failure")
            except ValueError:
                pass

        session.rollback.assert_awaited_once()
        session.commit.assert_not_awaited()

    asyncio.run(run_test())
