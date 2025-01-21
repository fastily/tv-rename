import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tv-rename",
    version="0.0.1",
    author="Fastily",
    author_email="fastily@users.noreply.github.com",
    description="Utility for batch renaming mangled season dirs and/or episode names",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fastily/tv-rename",
    project_urls={
        "Bug Tracker": "https://github.com/fastily/tv-rename/issues",
    },
    include_package_data=True,
    packages=setuptools.find_packages(include=["tv_rename"]),
    install_requires=["rich", "tvdb-v4-official"],
    entry_points={
        'console_scripts': ['tv_rename = tv_rename.__main__:_main', 'unmangle_episodes = tv_rename.unmangle:_main']
    },
    classifiers=[
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.13"
)
