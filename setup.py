from setuptools import setup, find_packages

setup(
    name="multicliswarm",
    version="1.0.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pydantic>=2.0.0",
        "mcp>=0.1.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        "pathspec>=0.11.0",
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
        "opentelemetry-exporter-otlp>=1.20.0",
        "duckduckgo-search>=6.0.0",
        "playwright>=1.40.0",
        "PyGithub>=2.1.0",
        "tenacity>=8.2.0",
        "chromadb>=0.4.0",
        "sentence-transformers>=2.2.0"
    ],
    entry_points={
        "console_scripts": [
            "multicliswarm=multicliswarm.cli:main",
            "multicliswarm-mcp=multicliswarm.mcp_server:main",
            "multicliswarm-ui=multicliswarm.web_ui:main",
            "multicliswarm-ci=multicliswarm.ci_cd_handler:main",
        ],
    },
)
