import json
import logging
from ollama import ps, pull, chat, ProcessResponse, ChatResponse
from datetime import datetime
from pydantic import BaseModel

class AI:
    def __init__(self, model, logger = None):
        if logger is None:
            raise ValueError("Logger cannot be None")
        if model is None:
            raise ValueError("Ollama Model cannot be None")
        
        self._logger = logger
        self._model = model
        self.systemprompt = 'You are a personalized document analyzer. Your task is to analyze documents and extract relevant information. \
            \
            Analyze the document content which you will get in the next message.\
            After that I will send you the instruction which information you need to extract.\
            Be Short and concise and answer without any other additional information and without control characters. \
            Correct spelling or other errors in your answer. Return the info in JSON format. '
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
        return (jsonvalue['info'])
    
    def selfCheck(self):
        start = datetime.now()
        response = pull(self._model, stream=True)
        self._logger.debug("Check if the Model is already pulled.")
        progress_states = set()
        try:
            for progress in response:
                if progress.get('status') and progress['status'].startswith("pulling manifest"):
                    self._logger.info(f"Model {self._model} not found. Pulling the model")
                self._logger.debug(progress.get('status'))
                if progress.get('status') in progress_states:
                    continue
        except Exception as X:
            self._logger.error(f"Something went wrong. Maybe the model {self._model} does not exist?")
            return False
        progress_states.add(progress.get('status'))
        self._logger.info(progress.get('status'))
        end = datetime.now()
        duration = end-start
        self._logger.debug("It took me " + str(duration) + " to pull the model")
        self._logger.debug('\n')
        start = datetime.now()
        self._logger.debug('Waiting for model to load... \n')
        end = datetime.now()
        duration = end-start
        self._logger.debug("It took me " + str(duration) + " to load the model")

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
        duration = end-start
        self._logger.debug("It took me " + str(duration) + " to greet you")
        return True;

class info(BaseModel):
    info: str