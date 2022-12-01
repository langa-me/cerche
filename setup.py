from importlib_metadata import entry_points
from setuptools import setup, find_packages
from pathlib import Path

with open("requirements.txt") as f:
    required = f.read().splitlines()

if __name__ == "__main__":
    with Path(Path(__file__).parent, "README.md").open(encoding="utf-8") as file:
        long_description = file.read()

    setup(
        name="cerche",
        author="Langame LLC",
        packages=find_packages(),
        include_package_data=True,
        entry_points={"console_scripts": ["cerche = cerche:main"]},
        version="0.2.1",
        description="",
        long_description=long_description,
        long_description_content_type="text/markdown",
        data_files=[(".", ["README.md"])],
        install_requires=required,
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3.6",
        ],
        extras_require={"datasets": ["datasets", "gcsfs", "autofaiss"]},
    )
