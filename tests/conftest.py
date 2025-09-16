"""Pytest configuration and fixtures"""

import os
import time

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def db_engine():
    """Create a test database engine."""
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/pseudoscribe")
    engine = create_engine(db_url)

    # Retry connection
    for _ in range(10):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except OperationalError:
            time.sleep(1)
    else:
        pytest.fail("Could not connect to the database.")

    # Create tables
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS public.tenant_configurations (tenant_id VARCHAR(255) PRIMARY KEY, schema_name VARCHAR(255) UNIQUE, display_name VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
        conn.commit()

    yield engine

    # Clean up
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS public.tenant_configurations CASCADE"))
        conn.commit()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a new database session for each test, with cleanup."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()

    yield session

    # Clean up tables
    session.execute(text("DELETE FROM public.tenant_configurations"))
    session.commit()
    session.close()
