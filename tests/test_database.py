import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from bookflow.app.models import (
    Organization,
    OrganizationMember,
    OrganizationRole,
    User,
)


def test_create_user_with_organization_membership(
    db_session: Session,
):
    unique_id = uuid.uuid4().hex

    user = User(
        email=f"test-{unique_id}@example.com",
        password_hash="fake-password-hash",
    )

    organization = Organization(
        name="Test Organization",
        slug=f"test-organization-{unique_id}",
    )

    membership = OrganizationMember(
        user=user,
        organization=organization,
        role=OrganizationRole.OWNER,
    )

    db_session.add(membership)
    db_session.flush()

    saved_membership = db_session.scalar(
        select(OrganizationMember)
        .where(OrganizationMember.id == membership.id)
    )

    assert saved_membership is not None
    assert saved_membership.user.email == user.email
    assert saved_membership.organization.name == "Test Organization"
    assert saved_membership.role == OrganizationRole.OWNER