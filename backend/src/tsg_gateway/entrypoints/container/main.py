"""Run the API with uvicorn (local development and container hosting)."""

import uvicorn

from tsg_gateway.settings import AppEnv, get_settings


def main() -> None:
    """Start uvicorn. Reloads on code changes when running locally."""
    settings = get_settings()
    uvicorn.run(
        "tsg_gateway.entrypoints.api.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=settings.app_env is AppEnv.LOCAL,
        access_log=False,
        log_config=None,
    )


if __name__ == "__main__":
    main()
