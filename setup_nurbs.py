"""
Cython 加速模块构建脚本

用法：
    cd EVOLUTION_AI_DEMO && python setup_nurbs.py build_ext --inplace
    或运行 build_cython.sh
"""
import os
import sys
import numpy as np
from setuptools import setup, Extension

try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

extensions = []

# NURBS 加速内核
pyx_nurbs = os.path.join(BASE_DIR, 'algorithm_model', 'freeform', '_nurbs_cy.pyx')
if os.path.exists(pyx_nurbs):
    if USE_CYTHON:
        extensions.append(
            Extension(
                'algorithm_model.freeform._nurbs_cy',
                sources=[pyx_nurbs],
                include_dirs=[np.get_include()],
                define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
            )
        )
    else:
        # 尝试用已编译的 .c 文件
        c_nurbs = pyx_nurbs.replace('.pyx', '.c')
        if os.path.exists(c_nurbs):
            extensions.append(
                Extension(
                    'algorithm_model.freeform._nurbs_cy',
                    sources=[c_nurbs],
                    include_dirs=[np.get_include()],
                    define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
                )
            )

# 质量评估加速内核
pyx_quality = os.path.join(BASE_DIR, 'algorithm_model', 'surface_quality', '_quality_cy.pyx')
if os.path.exists(pyx_quality):
    if USE_CYTHON:
        extensions.append(
            Extension(
                'algorithm_model.surface_quality._quality_cy',
                sources=[pyx_quality],
                include_dirs=[np.get_include()],
                define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
            )
        )
    else:
        c_quality = pyx_quality.replace('.pyx', '.c')
        if os.path.exists(c_quality):
            extensions.append(
                Extension(
                    'algorithm_model.surface_quality._quality_cy',
                    sources=[c_quality],
                    include_dirs=[np.get_include()],
                    define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
                )
            )

if USE_CYTHON and extensions:
    ext_modules = cythonize(
        extensions,
        compiler_directives={
            'boundscheck': False,
            'wraparound': False,
            'cdivision': True,
            'language_level': '3',
        }
    )
elif extensions:
    ext_modules = extensions
else:
    ext_modules = []
    print("[setup_nurbs] WARNING: No .pyx files found and Cython not available. Nothing to build.")

setup(
    name='nurbs_cython_accel',
    ext_modules=ext_modules,
)
