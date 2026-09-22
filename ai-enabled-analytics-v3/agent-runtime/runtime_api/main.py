"""Default ASGI entry point.

Production composition should call create_app(agent_host) and provide a fully
configured Agent Host. The default application intentionally has no host and
returns a structured 503 response for host-dependent endpoints.
"""

from .app import create_app


app = create_app()
