# Social Media Post Generator Package

This project contains a Steamship Package that creates a social media post describing your new youtube video.

Web demo:

## Usage

```python
import time

from steamship import Steamship
from steamship.base import TaskState


instance = Steamship.use("audio-description", "my-workspace-name")

url = "<url to mp3 file>"
transcribe_task = instance.invoke("analyze_youtube", url=url)
task_id = transcribe_task["task_id"]
status = transcribe_task["status"]

# Wait for completion
retries = 0
while retries <= 100 and status != TaskState.succeeded:
    response = instance.invoke("status", task_id=task_id)
    status = response["status"]
    if status == TaskState.failed:
        print(f"[FAILED] {response['status_message']")
        break

    print(f"[Try {retries}] Transcription {status}.")
    if status == TaskState.succeeded:
        break
    time.sleep(2)
    retries += 1

# Get the Generated Text
TEXT = response["file"]
```

## Developing

Development instructions are located in [DEVELOPING.md](DEVELOPING.md)

## Deploying

Deployment instructions are located in [DEPLOYING.md](DEPLOYING.md)
