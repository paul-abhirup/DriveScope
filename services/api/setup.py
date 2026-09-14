from setuptools import setup, find_packages

setup(
    name="drivescope-api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.110.0",
        "uvicorn[standard]>=0.28.0",
        "pydantic-settings>=2.2.0",
        "sqlalchemy>=2.0.28",
        "drivescope-schema>=0.1.0",
        "drivescope-vla-sdk>=0.1.0"
    ],
)
