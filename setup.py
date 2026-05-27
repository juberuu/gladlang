import os
from setuptools import setup, find_packages

version_file = os.path.join("src", "gladlang", "version.py")
with open(version_file, encoding="utf-8") as f:
    exec(f.read())

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="gladlang",
    version=__version__,
    description="The GladLang Interpreter",
    long_description=long_description,
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
