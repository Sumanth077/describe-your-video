"""Test zendesk-ticket-urgency via unit test."""
import pytest
from steamship import File, Steamship

from src.api import AudioDescriptionApp
from tests.utils import (
    TEST_URL,
    check_analyze_response,
    check_query_response,
    prep_workspace,
)


@pytest.fixture()
def audio_description_app(steamship_client: Steamship):
    """Instantiate an instance of AudioTranscriptionPackage."""
    return AudioDescriptionApp(client=steamship_client, config={})


def test_analyze_youtube(audio_description_app: AudioDescriptionApp) -> None:
    """Test the analyze_youtube endpoint."""
    response = audio_description_app.analyze_youtube(url=TEST_URL)
    check_analyze_response(audio_description_app, response)


def test_query(steamship_client: Steamship, audio_description_app: AudioDescriptionApp) -> None:
    """Test the query endpoint."""
    prep_workspace(steamship_client)

    response = audio_description_app.query(query='filetag and kind "test_file"')

    check_query_response(response, File, "test_file", "file123")
