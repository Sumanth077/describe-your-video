"""Collection of utility function to support testing."""
import base64
import time
from datetime import datetime
from functools import partial
from pathlib import Path
from tests import TEST_DATA
from typing import List, Type, Union
from uuid import uuid4

from pydantic import parse_obj_as
from steamship import Block, File, PackageInstance, Steamship, Tag, Workspace
from steamship.base import TaskState
from steamship.data.workspace import SignedUrl
from steamship.invocable import InvocableResponse
from steamship.utils.signed_urls import upload_to_signed_url

from src.api import AudioDescriptionApp

TEST_URL = "https://www.youtube.com/watch?v=Nu0WXRXUfAk"


def check_analyze_response(package: Union[AudioDescriptionApp, PackageInstance], response):
    """Verify the response returned by the analyze endpoint."""
    response = _check_analyze_response(response)

    task_id = response["task_id"]
    get_status = (
        package.get_status
        if isinstance(package, AudioDescriptionApp)
        else partial(package.invoke, path="status")
    )
    response = get_status(task_id=task_id)
    response = response.data if not isinstance(response, dict) else response
    n_retries = 0
    while n_retries <= 100 and response["status"] not in (TaskState.succeeded, TaskState.failed):
        time.sleep(2)
        response = get_status(task_id=task_id)
        response = _check_analyze_response(response)
        n_retries += 1

    assert response["status"] == TaskState.succeeded
    assert "file" in response
    file = response["file"]


def _check_file(file):
    assert file.blocks is not None
    assert len(file.blocks) > 0
    block = file.blocks[0]
    assert block.tags is not None
    assert len(block.tags) > 0


def _check_analyze_response(response):
    response = response.data if not isinstance(response, dict) else response
    assert response is not None
    assert "task_id" in response
    assert "status" in response
    assert response["status"] in (
        TaskState.succeeded,
        TaskState.failed,
        TaskState.running,
        TaskState.waiting,
    )
    if response["status"] == TaskState.succeeded:
        assert "file" in response
    return response


def load_file(filename: Path) -> str:
    """Load b64 encoded audio from test data."""
    audio_path = TEST_DATA / "inputs" / filename
    with audio_path.open("rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def upload_audio_file(client: Steamship, file: Path, mime_type: str) -> str:
    """Upload an audio file to the default workspace."""
    media_format = mime_type.split("/")[1]
    unique_file_id = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{uuid4()}.{media_format}"
    workspace = Workspace.get(client=client)

    writing_signed_url = workspace.create_signed_url(
        SignedUrl.Request(
            bucket=SignedUrl.Bucket.APP_DATA,
            filepath=unique_file_id,
            operation=SignedUrl.Operation.WRITE,
        )
    ).signed_url
    audio_path = TEST_DATA / "inputs" / file
    upload_to_signed_url(writing_signed_url, filepath=audio_path)
    reading_signed_url = workspace.create_signed_url(
        SignedUrl.Request(
            bucket=SignedUrl.Bucket.APP_DATA,
            filepath=unique_file_id,
            operation=SignedUrl.Operation.READ,
        )
    ).signed_url
    return reading_signed_url


def check_query_response(
    response: InvocableResponse, expected_type: Type[Union[File, Tag]], kind: str, name: str
) -> None:
    """Verify the response returned by the query endpoint."""
    response = response.data if not isinstance(response, list) else response
    assert response is not None
    assert isinstance(response, list)
    assert len(response) > 0
    if not isinstance(response[0], expected_type):
        return_objects = parse_obj_as(List[expected_type], response)
    else:
        return_objects = response
    assert isinstance(return_objects[0], expected_type)
    tag = return_objects[0].tags[0] if expected_type is File else return_objects[0]
    assert tag.kind == kind
    assert tag.name == name


def prep_workspace(client: Steamship):
    """Prepare workspace by removing all files and adding a test file."""
    for file in File.query(client, tag_filter_query="all").files:
        file.delete()
    File.create(
        client,
        tags=[Tag.CreateRequest(kind="test_file", name="file123")],
        blocks=[Block.CreateRequest(tags=[Tag.CreateRequest(kind="test_block", name="block123")])],
    )