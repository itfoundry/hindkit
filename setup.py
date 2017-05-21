#!/usr/bin/env AFDKOPython
import setuptools
setuptools.setup(
    name = "hindkit",
    version = "1.0.0",
    url = "https://github.com/itfoundry/hindkit",
    author = "Liang Hai",
    author_email = "lianghai@gmail.com",
    license="MIT",
    package_dir = {"": "lib"},
    py_modules = [
        "getKerningPairsFromFEA"
        "WriteFeaturesKernFDK",
        "WriteFeaturesMarkFDK",
    ],
    packages = [
        "hindkit",
        "hindkit.objects",
    ],
    package_data = {
        "hindkit": [
            "data/*.txt",
            "data/premade/*/GlyphOrderAndAliasDB",
            "data/premade/*/features/*.fea",
        ],
    },
)
