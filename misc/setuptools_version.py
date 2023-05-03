import os

from pybind11.setup_helpers import Pybind11Extension
from setuptools import setup

cmdstan_path = os.environ["CMDSTAN"]

include_dirs = [
    cmdstan_path + "/stan/lib/stan_math/lib/tbb_2020.3/include",
    cmdstan_path + "/stan/src",
    cmdstan_path + "/lib/rapidjson_1.1.0/",
    cmdstan_path + "/stan/lib/stan_math/",
    cmdstan_path + "/stan/lib/stan_math/lib/eigen_3.4.0",
    cmdstan_path + "/stan/lib/stan_math/lib/boost_1.78.0",
    cmdstan_path + "/stan/lib/stan_math/lib/sundials_6.1.1/include",
    cmdstan_path + "/stan/lib/stan_math/lib/sundials_6.1.1/src/sundials",
]

library_dirs = [cmdstan_path + "/stan/lib/stan_math/lib/tbb"]
runtime_dirs = [
    cmdstan_path + "/stan/lib/stan_math/lib/tbb",
    cmdstan_path + "/stan/lib/stan_math/lib/sundials_6.1.1/lib/",
]

# see https://setuptools.pypa.io/en/latest/userguide/ext_modules.html#setuptools.Extension
basic = Pybind11Extension(
    "basic",
    sources=["basic.cpp"],
    include_dirs=include_dirs,
    define_macros=[("_REENTRANT", None), ("BOOST_DISABLE_ASSERTS", None)],
    libraries=[
        "tbb",
        "sundials_nvecserial",
        "sundials_cvodes",
        "sundials_idas",
        "sundials_kinsol",
    ],
    library_dirs=library_dirs,
    runtime_library_dirs=runtime_dirs,
)

# running setuptools_version.py build will build basic.stan
setup(ext_modules=[basic])
