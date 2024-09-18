from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_scoped_session, async_sessionmaker

from asyncio import current_task

from parser_domain.core.config import settings


class DataBaseHelper:
    def __init__(self, url: str, echo: bool = False):
        self.engine = create_async_engine(
            url=url,
            echo=echo
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )
    
    async def session_depends(self) -> AsyncSession:
        async with self.session_factory() as session:
            yield session

db_helper = DataBaseHelper(
    url=settings.db.url,
    echo=settings.db.echo
)