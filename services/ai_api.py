import json
import logging
from ollama import ps, pull, chat, ProcessResponse, ChatResponse
from datetime import datetime
from pydantic import BaseModel

class AI:
    # Initializes the AI class for handling document analysis.
    # Parameters:
    # - model (str): The name of the Ollama model to use.
    # - logger (logging.Logger): Logger instance for logging.
    def __init__(self, model, logger=None):
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

    # Processes a document and extracts information based on a given prompt.
    # Parameters:
    # - content (str): The document content to analyze.
    # - prompt (str): The specific instruction on what information to extract.
    # Returns:
    # - dict: Extracted information in JSON format.
    def getResponse(self, content, prompt):
        messages = [
            {
                'role': 'system',
                'content': self.systemprompt,
            },
            {
                'role': 'system',
                'content': content,
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ]

        response = chat(self._model, messages=messages, format=info.model_json_schema())
        jsonvalue = json.loads(response['message']['content'])
        self._logger.debug(f"The AI returned: {jsonvalue['info']}")
        return jsonvalue['info']
    
    # Checks if the AI model is available and loads it if necessary.
    # Returns:
    # - bool: True if the model is successfully loaded, otherwise False.
    def selfCheck(self):
        start = datetime.now()
        response = pull(self._model, stream=True)
        self._logger.debug("Check if the model is already pulled.")

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
        self._logger.debug("Waiting for model to load... \n")
        end = datetime.now()
        duration = end - start
        self._logger.debug(f"It took {duration} to load the model")

        # Run a simple test command to check if the model is responsive
        response: ProcessResponse = ps()
        start = datetime.now()

        response: ChatResponse = chat(model=self._model, messages=[
            {
                'role': 'user',
                'content': 'Say Hello Gemma',
            },
        ])

        self._logger.debug(response['message']['content'])
        end = datetime.now()
        duration = end - start
        self._logger.debug(f"It took {duration} to greet you")
        return True

# Defines the expected response format for AI output.
class info(BaseModel):
    info: str