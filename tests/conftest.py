import pytest
import tempfile
import shutil
from rest_framework.test import APIClient
from django.conf import settings


@pytest.fixture
def api_client():
    """Return an unauthenticated DRF APIClient instance."""
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    """Return an APIClient authenticated with a created user.

    Tests using Django's `APITestCase` will continue to work; this fixture is
    available for future pytest-style tests.
    """
    from django.contrib.auth.models import User

    client = APIClient()
    user = User.objects.create_user(username='pytest_user', password='password123')
    client.login(username='pytest_user', password='password123')
    return client


@pytest.fixture(autouse=True)
def media_root(settings, tmpdir):
    """
    Automatically use a temporary directory for MEDIA_ROOT in all tests.
    This ensures tests don't interfere with real media files and provides
    proper cleanup after each test.
    """
    settings.MEDIA_ROOT = str(tmpdir)
    return tmpdir
