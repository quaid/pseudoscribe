from setuptools import setup, find_packages

setup(
    name="pseudoscribe",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "SQLAlchemy>=2.0.27",
        "alembic>=1.13.1",
        "psycopg2-binary>=2.9.9",
    ],
    python_requires=">=3.9",
    extras_require={
        "test": ["pytest", "pytest-asyncio", "httpx", "pytest-mock"],
    },
)
