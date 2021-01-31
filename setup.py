#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file inspired by https://github.com/navdeep-G/setup.py

# Note: To use the 'upload' functionality of this file, you must:
#   $ pipenv install twine --dev

import io
import os
import sys
from shutil import Error, rmtree

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = "somweb"
DESCRIPTION = "SOMweb client. Open/close Garage doors produced by SOMMER (base+/pro+/tiga/tiga+/barrier systems)"
URL = "https://github.com/taarskog/pysomweb"
EMAIL = "somweb@heiigjen.com"
AUTHOR = "Trond Aarskog"
REQUIRES_PYTHON = ">=3.6.0"
VERSION = None  # Version taken from package
LICENSE = "MIT"
KEYWORDS = [
    "sommer",
    "SOMweb",
    "garage door",
    "home assistant",
    "home automation",
    "heiigjen",
]

# Trove classifiers - Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
CLASSIFIERS = [
    # Choose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: MIT License",
    "Intended Audience :: Developers",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Operating System :: OS Independent",
    "Topic :: Home Automation",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

# What packages are optional?
EXTRAS = {
    # 'fancy feature': ['django'],
}

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

# with open("LICENSE") as f:
#     license = f.read()

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    project_slug = NAME.lower().replace("-", "_").replace(" ", "_")
    with open(os.path.join(here, project_slug, "__version__.py")) as f:
        exec(f.read(), about)
else:
    # about["__version__"] = VERSION
    raise Error("Required file missing. Package should have a __VERSION__ file!")

# What packages are required for this module to be executed?
# Load the package's requirements.txt as an array.

with open(os.path.join(here, "requirements.txt"), encoding="utf-8") as f:
    REQUIRED = f.readlines()
if not REQUIRED:
    raise Error("Required file missing. Root should have a requirements.txt file!")


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print("\033[1m{0}\033[0m".format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status("Removing previous builds…")
            rmtree(os.path.join(here, "dist"))
        except OSError:
            pass

        self.status("Building Source and Wheel distribution…")
        os.system(f"{sys.executable} setup.py sdist bdist_wheel")

        self.status("Uploading the package to PyPI via Twine…")
        os.system("twine upload dist/*")

        self.status("Pushing git tags…")
        os.system("git tag v{0}".format(about["__version__"]))
        os.system("git push --tags")

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    download_url=f"{URL}/archive/v{about['__version__']}.tar.gz",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    keywords=KEYWORDS,
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license=LICENSE,
    classifiers=CLASSIFIERS,
    # $ setup.py publish support.
    cmdclass={
        "upload": UploadCommand,
    },
)
