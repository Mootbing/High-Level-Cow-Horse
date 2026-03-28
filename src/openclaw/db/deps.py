from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw.db.session import get_session

DBSession = Annotated[AsyncSession, Depends(get_session)]
