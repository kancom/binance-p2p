from fastapi import FastAPI

import p2p.api.http_api as api
from p2p.wiring import Container


def create_app() -> FastAPI:
    container = Container()

    app = FastAPI()
    app.include_router(api.router)
    return app


app = create_app()
