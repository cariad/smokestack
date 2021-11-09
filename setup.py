from pathlib import Path

from setuptools import setup  # pyright: reportMissingTypeStubs=false

from smokestack.version import get_version

readme_path = Path(__file__).parent / "README.md"

with open(readme_path, encoding="utf-8") as f:
    long_description = f.read()

classifiers = [
    "Environment :: Console",
    "License :: OSI Approved :: MIT License",
    "Natural Language :: English",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Topic :: Utilities",
    "Typing :: Typed",
]

version = get_version()

if "a" in version:
    classifiers.append("Development Status :: 3 - Alpha")
elif "b" in version:
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
        "ansiscape >=1.0.0,   <2.0",
        "boto3     >=1.18.59, <2.0",
        "cfp       ==1.0.0a3",
        "pyyaml    >=6.0,     <7.0",
        "stackdiff >=1.0,     <2.0",
        "stackwhy  >=1.0.1,   <2.0",
        "tabulate  >=0.8.9 ,  <1.0",
    ],
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    name="smokestack",
    packages=[
        "smokestack",
        "smokestack.abc",
        "smokestack.cli",
        "smokestack.exceptions",
        "smokestack.models",
        "smokestack.parameters",
        "smokestack.version",
    ],
    package_data={
        "smokestack": ["py.typed"],
        "smokestack.abc": ["py.typed"],
        "smokestack.cli": ["py.typed"],
        "smokestack.exceptions": ["py.typed"],
        "smokestack.models": ["py.typed"],
        "smokestack.parameters": ["py.typed"],
        "smokestack.version": ["py.typed"],
    },
    python_requires=">=3.8",
    url="https://github.com/cariad/smokestack",
    version=version,
)
