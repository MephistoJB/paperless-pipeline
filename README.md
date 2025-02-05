This is a dockerbased processor, which is meant to be triggered by paperless-ngx via webhook.

It is ment to be installed as a docker image via dockerhub which can be pulled by: docker pull mephistojb/paperless-ngx-ollamaprocessor:latest

There are mandatory environment variables which have to be set:

OLLAMA_HOST (E.g. OLLAMA_HOST = http://192.168.1.56:11434)

OLLAMA_MODEL (E.g. OLLAMA_MODEL = gemma2)
PAPERLESS_BASE_URL (E.g.) PAPERLESS_BASE_URL = http://192.168.1.56:8000
AUTH_TOKEN (E.g. AUTH_TOKEN = xyzausdhfspdgsdfojndfübjndfbüodfbüdofi) look here for more info https://docs.paperless-ngx.com/api/#authorization

Optional you can also set
LOG_LEVEL (E.g. LOG_LEVEL = DEBUG)
