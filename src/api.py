"""Package that transcribes the audio and video Files into Text"""
import json
from typing import Type

from pydantic import HttpUrl
from steamship import File, Block, MimeTypes
from steamship.base import Task, TaskState
from steamship.invocable import Config, InvocableResponse, PackageService, create_handler, post

PRIORITY_LABEL = "priority"


class AudioDescriptionApp(PackageService):
    """Package that transcribes the audio and video Files into Text"""

    YOUTUBE_FILE_IMPORTER_HANDLE = "youtube-file-importer"
    S2T_BLOCKIFIER_HANDLE = "deepgram-s2t-blockifier-2"
    PROMPT_GENERATION_HANDLE = "prompt-generation-default"

    class AudioDescriptionAppConfig(Config):
        """Config object containing required configuration parameters to initialize a AudioAnalyticsApp."""

        pass

    def config_cls(self) -> Type[Config]:
        """Return the Configuration class."""
        return self.AudioDescriptionAppConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.youtube_importer = self.client.use_plugin(
            plugin_handle=self.YOUTUBE_FILE_IMPORTER_HANDLE
        )
        self.s2t_blockifier = self.client.use_plugin(plugin_handle=self.S2T_BLOCKIFIER_HANDLE)
        self.generator = self.client.use_plugin(plugin_handle=self.PROMPT_GENERATION_HANDLE,
                                                instance_handle="my-new-instance",
                                                config={"temperature": 0.7, "max_words": 250,
                                                        "model": "text-davinci-003"})

    @post("analyze_youtube")
    def analyze_youtube(self, url: HttpUrl) -> InvocableResponse:
        """Transcribe and analyze a Youtube video."""
        file_create_task = File.create_with_plugin(
            self.client, plugin_instance=self.youtube_importer.handle, url=url
        )
        file_create_task.wait(max_timeout_s=5 * 60)  # Wait for 5 minutes
        file = file_create_task.output
        return self._get_audio_highlights(file)

    @post("status")
    def get_status(self, task_id: str):
        """Get a file created by a task using the task ID."""
        task = Task.get(self.client, _id=task_id)
        if task.state != TaskState.succeeded:
            return InvocableResponse(json={"task_id": task.task_id, "status": task.state})
        else:
            file_id = json.loads(task.input)["id"]
            file = File.get(self.client, file_id)
            summary = file.dict()['blocks'][0]['tags'][0]['name']
            generated_text = self._generate(summary)
            return InvocableResponse(
                json={"task_id": task.task_id, "status": task.state, "file": generated_text}
            )

    @post("query")
    def query(self, query: str) -> InvocableResponse:
        """Query the files in the workspace."""
        return InvocableResponse(json=File.query(self.client, tag_filter_query=query).files)

    def _get_audio_highlights(self, file) -> InvocableResponse:
        blockify = file.blockify(plugin_instance=self.s2t_blockifier.handle)
        return InvocableResponse(
            json={"task_id": blockify.task_id, "status": blockify.state}
        )

    @post("generate")
    def _generate(self, audio_summary) -> InvocableResponse:
        prompt = "Generate a Linkedin Post describing my latest video. This is the Summary of the Video: {}".format(
            audio_summary)
        file = File.create(self.client, mime_type=MimeTypes.TXT, blocks=[Block.CreateRequest(text=prompt)])
        file.tag(self.generator.handle).wait()
        file = file.refresh()

        return file.blocks[0].tags[0].value['string-value']


handler = create_handler(AudioDescriptionApp)
