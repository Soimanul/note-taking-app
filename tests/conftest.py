import pytest
from rest_framework.test import APIClient


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
