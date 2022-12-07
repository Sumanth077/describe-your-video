"""Test audio-transcription package via integration test."""
import random
import string

import pytest
from steamship import File, PackageInstance, Steamship

from tests.conftest import PACKAGE_HANDLE
from tests.utils import (
    TEST_URL,
    check_analyze_response,
    check_query_response,
    prep_workspace
)


def random_name() -> str:
    """Returns a random name suitable for a handle that has low likelihood of colliding with another.

    Output format matches test_[a-z0-9]+, which should be a valid handle.
    """
    letters = string.digits + string.ascii_letters
    return f"test_{''.join(random.choice(letters) for _ in range(10))}".lower()  # noqa: S311


@pytest.fixture()
def package_instance(steamship_client: Steamship) -> PackageInstance:
    """Instantiate an instance of the audio-description package."""
    package_instance = steamship_client.use(package_handle=PACKAGE_HANDLE, instance_handle=random_name(), config={})
    assert package_instance is not None
    assert package_instance.id is not None
    return package_instance


def test_analyze_youtube(package_instance: PackageInstance) -> None:
    """Test the analyze_youtube endpoint."""
    response = package_instance.invoke("analyze_youtube", url=TEST_URL)
    check_analyze_response(package_instance, response)


def test_query(steamship_client: Steamship, package_instance: PackageInstance) -> None:
    """Test the query endpoint."""
    prep_workspace(steamship_client)

    response = package_instance.invoke("query", query='filetag and kind "test_file"')
    check_query_response(response, File, "test_file", "file123")
