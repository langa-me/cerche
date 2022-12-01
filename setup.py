from setuptools import setup, find_packages

with open("requirements.txt") as f:
    required = f.read().splitlines()

if __name__ == "__main__":
    setup(
        name="cerche",
        author="Langame LLC",
        packages=find_packages(),
        include_package_data=True,
        entry_points={"console_scripts": ["cerche = cerche:main"]},
        version="0.2.3",
        description="",
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
