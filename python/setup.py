#!/usr/bin/env python
# -*- coding: utf-8 -*-

# NOTE 如果你想用`upload`功能，则需要在环境里安装`twine`

import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

here = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".."
)  # NOTE 这里因为我的基本路径是`setup.py`文件的上一层，因此额外往上走了一级

# 包的基本信息.
NAME = "JDistributer"
DESCRIPTION = "JDistributer Demo"
URL = "https://github.com/ZhengqiaoWang/JDistributer"
EMAIL = "me@zhengqiao.wang"
AUTHOR = "ZhengqiaoWang"
REQUIRES_PYTHON = ">=3.6.0"

# 代码库运行时的依赖
REQUIRED = [
    "redis",
    "hiredis",
]

# 可选安装什么依赖
EXTRAS = {
    # 'fancy feature': ['django'],
}
# 将ChangeLog第一行读成VERSION
try:
    with io.open(os.path.join(here, "ChangeLog")) as f:
        VERSION = f.readline().strip("\n").strip()
except FileNotFoundError:
    VERSION = "0.1.0"  # 如果没有ChangeLog，则在这里设置版本

# 下面的基本上不怎么动，除非你要修改协议

# 将README.md文件读成long-description
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

about = {}
about["__version__"] = VERSION


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

        self.status("Building Source and Wheel (universal) distribution…")
        os.system("{0} setup.py sdist bdist_wheel --universal".format(sys.executable))

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
    packages=find_packages(
        exclude=["tests", "*.tests", "*.tests.*", "tests.*", "ut", "example"]
    ),
    # If your package is a single module, use this instead of 'packages':
    # py_modules=['mypackage'],
    # entry_points={
    #     'console_scripts': ['mycli=mymodule:cli'],
    # },
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license="MIT",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    # $ setup.py publish support.
    cmdclass={
        "upload": UploadCommand,
    },
)
