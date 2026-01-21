from collections.abc import Generator

from tastytrade import Session

from gex_app.core.gex_core import create_session


def get_tt_session() -> Generator[Session, None, None]:
    """
    Dependency that provides an authenticated Tastytrade session.
    It reuses the existing `create_session` logic from gex_app.
    """
    session = create_session()
    try:
        yield session
    finally:
        # In a real production app, we might want to keep the session alive
        # or manage a connection pool. For now, we destroy it or let it
        # expire to be safe, though create_session handles caching.
        pass
