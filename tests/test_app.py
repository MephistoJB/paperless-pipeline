import asyncio, pytest, sys, os
from unittest.mock import AsyncMock, MagicMock, patch
from app import app, main, stopServer, background_task, init_before_serving  # Consolidated imports

# Ensure the app's root directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

"""
Tests whether the application starts correctly.

Scenario:
- The application should initialize and start the server.

Expected Outcome:
- The initialization function is called once.
- The server startup function is called once.
- A log entry confirms successful startup.
"""
@pytest.mark.asyncio
async def test_main():
    with patch("app.init_before_serving", new_callable=AsyncMock) as mock_init, \
         patch("app.hypercorn.asyncio.serve", new_callable=AsyncMock) as mock_serve, \
         patch("app.logging.info") as mock_log, \
         patch("os.getenv", return_value="False"):

        await main()

        # Ensure initialization and server startup are executed
        mock_init.assert_called_once()
        mock_serve.assert_called_once()

        # Verify that a log message confirms successful startup
        mock_log.assert_any_call("Initialization complete, starting server...")

"""
Tests whether stopping the server functions correctly.

Scenario:
- The server should properly shut down when stopServer is called.

Expected Outcome:
- The shutdown event is set.
- A log entry confirms the shutdown process.
- The process exits with code 0.
"""
@pytest.mark.asyncio
async def test_stopServer():
    from app import shutdown_event  # Import the global shutdown event variable

    with patch("sys.exit") as mock_exit, patch("app.logging.info") as mock_log:
        shutdown_event.clear()  # Ensure the event is not set before execution
        task = asyncio.create_task(stopServer())  # Start stopServer as an asynchronous task
        await asyncio.sleep(1.1)  # Wait slightly longer than the delay in stopServer
        await task  # Ensure the task completes

        # Verify that the shutdown event was triggered
        assert shutdown_event.is_set(), "shutdown_event was not set"

        # Ensure a log message confirms the shutdown process
        mock_log.assert_called_with("Server is shutting down...")

        # Verify that the process exits with code 0
        mock_exit.assert_called_once_with(0)

"""
Tests whether the pre-server initialization completes successfully.

Scenario:
- The application should verify its configuration and initialize required services.

Expected Outcome:
- The configuration check function is called once.
- The paperless API is properly initialized.
- A background task is created.
- A log entry confirms successful initialization.
"""
@pytest.mark.asyncio
async def test_init_before_serving():
    with patch("app.config.checkConfig") as mock_check, \
         patch("app.logging.info") as mock_log, \
         patch("asyncio.create_task") as mock_create_task, \
         patch.dict(app.config, {"PAPERLESS_API": AsyncMock()}):  # Use AsyncMock for async operations

        await init_before_serving()

        # Ensure the configuration check function was called
        mock_check.assert_called_once_with(app)

        # Ensure the paperless API initialization was awaited
        await app.config["PAPERLESS_API"].initialize()

        # Verify that a background task was created
        mock_create_task.assert_called_once()

        # Ensure a log message confirms the pre-server initialization
        mock_log.assert_any_call("Pre-server initialization complete.")