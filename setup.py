import re
from pathlib import Path
from setuptools import setup, find_packages

version = re.search(
    r'^__version__\s*=\s*[\'"]([^\'"]+)[\'"]',
    Path("src/gladlang/version.py").read_text(encoding="utf-8"),
    re.MULTILINE,
).group(1)

setup(
    name="gladlang",
    version=version,
    description="The GladLang Interpreter",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Glad432",
    license="MIT",
    url="https://github.com/gladw-in/gladlang",
    project_urls={
        "Documentation": "https://gladlang.pages.dev/",
        "Source": "https://github.com/gladw-in/gladlang",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "gladlang = gladlang.__main__:main",
        ],
    },
    include_package_data=True,
)
