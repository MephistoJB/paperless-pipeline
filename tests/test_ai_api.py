import json, logging, pytest
from unittest.mock import patch, MagicMock
from services.ai_api import AI  # Import AI class for testing

# Initialize a logger for testing
logger = logging.getLogger("test_logger")

"""
Provides an AI instance for testing.

Returns:
- AI: An instance of the AI class using a test model.
"""
@pytest.fixture
def ai_instance():
    return AI(model="test_model", logger=logger)

"""
Tests the `getResponse` method with a mocked chat function.

Parameters:
- ai_instance (AI): The AI instance being tested.

Scenario:
- The AI should return a JSON response with extracted data.

Expected Outcome:
- The method returns the extracted value from the mock response.
"""
def test_getResponse(ai_instance):
    mock_response = {"message": {"content": json.dumps({"info": "Extracted Data"})}}

    # Mocking the AI chat response
    with patch("services.ai_api.chat", return_value=mock_response):
        response = ai_instance.getResponse("Test content", "Extract data")

        # Ensuring the extracted info is correctly returned
        assert response == "Extracted Data"

"""
Tests `getResponse` when the AI returns an invalid JSON response.

Parameters:
- ai_instance (AI): The AI instance being tested.

Scenario:
- The AI provides a non-parseable string.

Expected Outcome:
- The method raises a JSONDecodeError.
"""
def test_getResponse_invalid_json(ai_instance):
    mock_response = {"message": {"content": "Invalid JSON"}}

    # Mocking the AI response with invalid JSON
    with patch("services.ai_api.chat", return_value=mock_response):
        with pytest.raises(json.JSONDecodeError):
            ai_instance.getResponse("Test content", "Extract data")

"""
Tests the `selfCheck` method when the model loads successfully.

Parameters:
- ai_instance (AI): The AI instance being tested.

Scenario:
- The model is successfully pulled and responds to a test message.

Expected Outcome:
- The method returns True if the model loads successfully.
"""
def test_selfCheck_success(ai_instance):
    mock_pull_response = [{"status": "pulling manifest"}, {"status": "complete"}]
    mock_chat_response = {"message": {"content": "Hello Gemma"}}

    # Mocking successful pull and chat response
    with patch("services.ai_api.pull", return_value=mock_pull_response), \
         patch("services.ai_api.ps", return_value=MagicMock()), \
         patch("services.ai_api.chat", return_value=mock_chat_response):

        # Ensuring a successful model check returns True
        assert ai_instance.selfCheck() is True