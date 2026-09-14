from setuptools import setup, find_packages

setup(
    name="drivescope-vla-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "drivescope-schema>=0.1.0",
        "pydantic>=2.6.0",
    ],
)
