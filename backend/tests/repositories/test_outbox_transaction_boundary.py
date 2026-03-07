import asyncio
import uuid

import pytest
from sqlalchemy import select

from app.core.db.uow import UnitOfWork
from app.features.outbox.models import OutboxEvent
from app.features.outbox.repository import OutboxRepository
from app.features.rbac.models import Role
from app.features.rbac.repository import RBACRepository
from utils.testing_support.database import MockDatabase


def test_domain_write_and_outbox_event_commit_together(mock_database: MockDatabase) -> None:
    unique_token = uuid.uuid4().hex
    role_name = f"outbox-commit-{unique_token}"
    event_type = f"entity.role.created.{unique_token}"

    async def run_test() -> None:
        async with mock_database.Session() as session:
            unit_of_work = UnitOfWork(session=session)
            rbac_repository = RBACRepository(session=session)
            outbox_repository = OutboxRepository(session=session)

            async with unit_of_work:
                role = await rbac_repository.create_role(name=role_name)
                await outbox_repository.create_event(
                    aggregate_type="entity",
                    aggregate_id=str(role.id),
                    event_type=event_type,
                    payload={"entity_id": role.id, "entity_type": "role"},
                )

        async with mock_database.Session() as verification_session:
            role_query = select(Role).where(Role.name == role_name)
            role_row = await verification_session.execute(role_query)
            persisted_role = role_row.scalar_one_or_none()
            assert persisted_role is not None

            outbox_query = select(OutboxEvent).where(OutboxEvent.event_type == event_type)
            outbox_row = await verification_session.execute(outbox_query)
            persisted_event = outbox_row.scalar_one_or_none()
            assert persisted_event is not None
            assert persisted_event.aggregate_id == str(persisted_role.id)

    asyncio.run(run_test())


def test_domain_write_and_outbox_event_rollback_together_on_failure(mock_database: MockDatabase) -> None:
    unique_token = uuid.uuid4().hex
    role_name = f"outbox-rollback-{unique_token}"
    event_type = f"entity.role.created.{unique_token}"

    async def run_test() -> None:
        async with mock_database.Session() as session:
            unit_of_work = UnitOfWork(session=session)
            rbac_repository = RBACRepository(session=session)
            outbox_repository = OutboxRepository(session=session)

            with pytest.raises(RuntimeError, match="boom"):
                async with unit_of_work:
                    role = await rbac_repository.create_role(name=role_name)
                    await outbox_repository.create_event(
                        aggregate_type="entity",
                        aggregate_id=str(role.id),
                        event_type=event_type,
                        payload={"entity_id": role.id, "entity_type": "role"},
                    )
                    raise RuntimeError("boom")

        async with mock_database.Session() as verification_session:
            role_query = select(Role).where(Role.name == role_name)
            role_row = await verification_session.execute(role_query)
            assert role_row.scalar_one_or_none() is None

            outbox_query = select(OutboxEvent).where(OutboxEvent.event_type == event_type)
            outbox_row = await verification_session.execute(outbox_query)
            assert outbox_row.scalar_one_or_none() is None

    asyncio.run(run_test())
