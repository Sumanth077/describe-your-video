"""Test audio-transcription package via integration test."""
from tests.conftest import PACKAGE_HANDLE, config
from tests.utils import (
    TEST_URL,
    check_analyze_response,
    check_query_response,
    prep_workspace
)
from typing import Any, Dict

import pytest
from steamship import File, PackageInstance, Steamship


@pytest.fixture()
def package_instance(steamship_client: Steamship) -> PackageInstance:
    """Instantiate an instance of the audio-description package."""
    package_instance = steamship_client.use(package_handle=PACKAGE_HANDLE, instance_handle = "new-instance", config={})
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