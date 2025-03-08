import json
import logging
from ollama import ps, pull, chat, ProcessResponse, ChatResponse  # Consolidating imports
from datetime import datetime
from pydantic import BaseModel

"""
AI class for handling document analysis and extracting relevant information using the Ollama model.

Parameters:
- model (str): The name of the Ollama model to use.
- logger (logging.Logger): Logger instance for logging.
"""
class AI:
    def __init__(self, model: str, logger: logging.Logger):
        if logger is None:
            raise ValueError("Logger cannot be None")
        if model is None:
            raise ValueError("Ollama Model cannot be None")

        self._logger = logger
        self._model = model
        self.systemprompt = (
            "You are a personalized document analyzer. Your task is to analyze documents and extract relevant information. "
            "Analyze the document content which you will get in the next message. "
            "After that, I will send you the instruction which information you need to extract. "
            "Be short and concise and answer without any other additional information and without control characters. "
            "Correct spelling or other errors in your answer. Return the info in JSON format."
        )

    """
    Processes a document and extracts information based on a given prompt.

    Parameters:
    - content (str): The document content to analyze.
    - prompt (str): The specific instruction on what information to extract.

    Returns:
    - dict: Extracted information in JSON format.
    """
    def getResponse(self, content: str, prompt: str) -> dict:
        messages = [
            {'role': 'system', 'content': self.systemprompt},
            {'role': 'system', 'content': content},
            {'role': 'user', 'content': prompt},
        ]

        response = chat(self._model, messages=messages, format=Info.model_json_schema())
        jsonvalue = json.loads(response['message']['content'])
        self._logger.debug(f"The AI returned: {jsonvalue['info']}")
        return jsonvalue['info']

    """
    Checks if the AI model is available and loads it if necessary.

    Returns:
    - bool: True if the model is successfully loaded, otherwise False.
    """
    def selfCheck(self) -> bool:
        start = datetime.now()
        response = pull(self._model, stream=True)
        self._logger.debug("Checking if the model is already pulled.")

        progress_states = set()
        try:
            for progress in response:
                if progress.get('status') and progress['status'].startswith("pulling manifest"):
                    self._logger.info(f"Model {self._model} not found. Pulling the model")
                self._logger.debug(progress.get('status'))
                if progress.get('status') in progress_states:
                    continue
                progress_states.add(progress.get('status'))
        except Exception:
            self._logger.error(f"Something went wrong. Maybe the model {self._model} does not exist?")
            return False

        self._logger.info(progress.get('status'))
        end = datetime.now()
        duration = end - start
        self._logger.debug(f"It took {duration} to pull the model")

        # Wait for the model to load
        start = datetime.now()
        self._logger.debug("Waiting for model to load...")
        end = datetime.now()
        duration = end - start
        self._logger.debug(f"It took {duration} to load the model")

        # Run a simple test command to check if the model is responsive
        start = datetime.now()
        response: ProcessResponse = ps()

        response: ChatResponse = chat(
            model=self._model,
            messages=[{'role': 'user', 'content': 'Say Hello Gemma'}]
        )

        self._logger.debug(response['message']['content'])
        end = datetime.now()
        duration = end - start
        self._logger.debug(f"It took {duration} to greet you")

        return True

"""
Defines the expected response format for AI output.
"""
class Info(BaseModel):
    info: str