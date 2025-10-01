#!/usr/bin/env python3
"""
Setup script for Nocturnal Archive package
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "Production-ready AI Research Assistant with real data integration"

# Read requirements
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "aiohttp>=3.9.0",
            "groq>=0.4.0", 
            "python-dotenv>=1.0.0",
            "pydantic>=2.5.0"
        ]

setup(
    name="nocturnal-archive",
    version="1.0.0",
    author="Nocturnal Archive Team",
    author_email="contact@nocturnal.dev",
    description="Production-ready AI Research Assistant with real data integration",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Spectating101/nocturnal-archive",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "api": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "redis>=5.0.0",
            "asyncpg>=0.29.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "nocturnal-archive=nocturnal_archive.__init__:quick_start",
        ],
    },
    include_package_data=True,
    package_data={
        "nocturnal_archive": [
            "*.py",
            "*.txt",
            "*.md",
        ],
    },
    keywords=[
        "ai", "research", "finance", "academic", "papers", "sec", "edgar",
        "machine-learning", "data-analysis", "groq", "llm", "assistant"
    ],
    project_urls={
        "Bug Reports": "https://github.com/Spectating101/nocturnal-archive/issues",
        "Source": "https://github.com/Spectating101/nocturnal-archive",
        "Documentation": "https://github.com/Spectating101/nocturnal-archive#readme",
    },
)
