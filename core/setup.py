from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext, get_include

ext_modules = [
    Pybind11Extension(
        "go_engine",
        ["src/bindings.cpp"],
        include_dirs=[get_include()],
        cxx_std=17,
    ),
]

setup(
    name="go_engine",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)