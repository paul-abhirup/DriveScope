from setuptools import setup, find_packages

setup(
    name="drivescope-schema",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.6.0",
    ],
)
