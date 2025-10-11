#!/usr/bin/env python3
from setuptools import setup, find_packages
from pathlib import Path

readme_path = Path("README.md")
long_description = readme_path.read_text() if readme_path.exists() else "AI Research Assistant"

setup(
    name="cite-agent",
    version="1.0.4",
    author="Cite-Agent Team",
    author_email="contact@citeagent.dev",
    description="AI Research Assistant - Backend-Only Distribution",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Spectating101/cite-agent",
    packages=find_packages(exclude=["tests", "docs", "cite-agent-api", "cite_agent_api", "build*", "dist*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
        "aiohttp>=3.9.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "rich>=13.7.0",
        "keyring>=24.3.0",
        # NOTE: groq and cerebras NOT included - backend only
    ],
    entry_points={
        "console_scripts": [
            "cite-agent=cite_agent.cli:main",
            "nocturnal=cite_agent.cli:main",
        ],
    },
)
