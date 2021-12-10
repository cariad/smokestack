from pathlib import Path

from setuptools import setup  # pyright: reportMissingTypeStubs=false

from smokestack import __version__

readme_path = Path(__file__).parent / "README.md"

with open(readme_path, encoding="utf-8") as f:
    long_description = f.read()

classifiers = [
    "License :: OSI Approved :: MIT License",
    "Natural Language :: English",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Typing :: Typed",
]

if "a" in __version__:
    classifiers.append("Development Status :: 3 - Alpha")
elif "b" in __version__:
    classifiers.append("Development Status :: 4 - Beta")
else:
    classifiers.append("Development Status :: 5 - Production/Stable")

classifiers.sort()

setup(
    author="Cariad Eccleston",
    author_email="cariad@cariad.earth",
    classifiers=classifiers,
    description="CloudFormation stacks, beautifully",
    include_package_data=True,
    install_requires=[
        "ansiscape ~=1.0",
        "boto3     ~=1.20",
        "cfp       ~=1.0",
        "cline     ~=1.2",
        "pyyaml    ~=6.0",
        "stackdiff ~=1.1",
        "stackwhy  ~=1.0.1",
    ],
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    name="smokestack",
    packages=[
        "smokestack",
        "smokestack.ci",
        "smokestack.enums",
        "smokestack.exceptions",
        "smokestack.tasks",
        "smokestack.types",
    ],
    package_data={
        "smokestack": ["py.typed"],
        "smokestack.ci": ["py.typed"],
        "smokestack.enums": ["py.typed"],
        "smokestack.exceptions": ["py.typed"],
        "smokestack.tasks": ["py.typed"],
        "smokestack.types": ["py.typed"],
    },
    python_requires=">=3.8",
    url="https://github.com/cariad/smokestack",
    version=__version__,
)
