import mock
import pytest

from awx.main.migrations import _rbac as rbac
from awx.main.access import (
    BaseAccess,
    OrganizationAccess,
)
from django.apps import apps


@pytest.mark.django_db
def test_organization_migration_admin(organization, permissions, user):
    u = user('admin', False)
    organization.deprecated_admins.add(u)

    # Undo some automatic work that we're supposed to be testing with our migration
    organization.admin_role.members.remove(u)
    assert u not in organization.admin_role

    rbac.migrate_organization(apps, None)

    assert u in organization.admin_role

@pytest.mark.django_db
def test_organization_migration_user(organization, permissions, user):
    u = user('user', False)
    organization.deprecated_users.add(u)

    # Undo some automatic work that we're supposed to be testing with our migration
    organization.member_role.members.remove(u)
    assert u not in organization.read_role

    rbac.migrate_organization(apps, None)

    assert u in organization.read_role


@mock.patch.object(BaseAccess, 'check_license', return_value=None)
@pytest.mark.django_db
def test_organization_access_superuser(cl, organization, user):
    access = OrganizationAccess(user('admin', True))
    organization.deprecated_users.add(user('user', False))

    assert access.can_change(organization, None)
    assert access.can_delete(organization)

    org = access.get_queryset()[0]
    assert len(org.deprecated_admins.all()) == 0
    assert len(org.deprecated_users.all()) == 1


@mock.patch.object(BaseAccess, 'check_license', return_value=None)
@pytest.mark.django_db
def test_organization_access_admin(cl, organization, user):
    '''can_change because I am an admin of that org'''
    a = user('admin', False)
    organization.admin_role.members.add(a)
    organization.member_role.members.add(user('user', False))

    access = OrganizationAccess(a)
    assert access.can_change(organization, None)
    assert access.can_delete(organization)

    org = access.get_queryset()[0]
    assert len(org.admin_role.members.all()) == 1
    assert len(org.member_role.members.all()) == 1


@mock.patch.object(BaseAccess, 'check_license', return_value=None)
@pytest.mark.django_db
def test_organization_access_user(cl, organization, user):
    access = OrganizationAccess(user('user', False))
    organization.member_role.members.add(user('user', False))

    assert not access.can_change(organization, None)
    assert not access.can_delete(organization)

    org = access.get_queryset()[0]
    assert len(org.admin_role.members.all()) == 0
    assert len(org.member_role.members.all()) == 1