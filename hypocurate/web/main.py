"""The ASGI entry point: `uvicorn hypocurate.web.main:app`. Settings are read at start-up."""
from hypocurate.web.app import create_app

app = create_app()
