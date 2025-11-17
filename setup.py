"""
Setup script for building Cython extensions.

Usage:
    python setup.py build_ext --inplace
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

import platform

# Platform-specific optimization flags
extra_compile_args = ["-O3"]
if platform.system() != "Darwin":  # Not macOS
    extra_compile_args.append("-march=native")

extensions = [
    Extension(
        "bitboard_ops",
        ["bitboard_ops.pyx"],
        extra_compile_args=extra_compile_args,
        extra_link_args=["-O3"],
    ),
    Extension(
        "cython_moves",
        ["cython_moves.pyx"],
        extra_compile_args=extra_compile_args,
        extra_link_args=["-O3"],
        language="c++",  # C++ for better optimization
    )
]

setup(
    name="Chess Engine",
    version="1.0",
    description="High-performance chess engine with magic bitboards and Cython optimization",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': "3",
            'boundscheck': False,
            'wraparound': False,
            'cdivision': True,
            'initializedcheck': False,
            'nonecheck': False,
        },
        annotate=True,  # Generate HTML annotation files
    ),
    include_dirs=[np.get_include()],
    zip_safe=False,
)
