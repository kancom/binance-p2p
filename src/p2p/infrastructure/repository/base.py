from sqlalchemy.ext.asyncio import AsyncEngine


class AsyncRepo:
    class NotFound(Exception):
        pass

    def __init__(self, eng: AsyncEngine):
        self._engine = eng
