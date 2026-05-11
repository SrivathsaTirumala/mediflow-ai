from multiprocessing import Process

import uvicorn

from backend.app.config import get_settings


settings = get_settings()


def run_api() -> None:
    uvicorn.run(
        "backend.app.api:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


def run_a2a() -> None:
    uvicorn.run(
        "backend.app.a2a_server:a2a_app",
        host=settings.host,
        port=settings.a2a_safety_port,
        reload=False,
    )


if __name__ == "__main__":
    api_process = Process(target=run_api)
    a2a_process = Process(target=run_a2a)
    api_process.start()
    a2a_process.start()

    try:
        api_process.join()
        a2a_process.join()
    except KeyboardInterrupt:
        api_process.terminate()
        a2a_process.terminate()
        api_process.join()
        a2a_process.join()
