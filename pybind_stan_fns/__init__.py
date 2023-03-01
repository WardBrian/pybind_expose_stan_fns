import importlib
import os
import platform
import subprocess
import sys
import sysconfig
from distutils import sysconfig as dist_sysconfig
from pathlib import Path

import cmdstanpy
import pybind11

from . import preprocess


def get_pybind_includes():
    # copied from pybind11.__main__
    dirs = [
        sysconfig.get_path("include"),
        sysconfig.get_path("platinclude"),
        pybind11.get_include(),
    ]

    # Make unique but preserve order
    unique_dirs = []
    for d in dirs:
        if d and d not in unique_dirs:
            unique_dirs.append(d)
    return unique_dirs


CMDSTAN = Path(cmdstanpy.cmdstan_path())
STANC = CMDSTAN / "bin" / "stanc"

CPP_DEFINES = ["_REENTRANT", "BOOST_DISABLE_ASSERTS"]

LIBRARIES = [
    "tbb",
    "sundials_nvecserial",
    "sundials_cvodes",
    "sundials_idas",
    "sundials_kinsol",
    "pthread",
]

CMDSTAN_SUB_INCLUDES = [
    ("stan", "src"),
    ("stan", "lib", "rapidjson_1.1.0"),
    ("stan", "lib", "stan_math"),
    ("stan", "lib", "stan_math", "lib", "eigen_3.3.9"),
    ("stan", "lib", "stan_math", "lib", "boost_1.78.0"),
]

OTHER_INCLUDES = []

CXX_FLAGS = [
    "-std=c++1y",
    "-O3",
    "-Wno-sign-compare",
    "-Wno-deprecated-builtins",
    "-Wno-ignored-attributes",
    "-shared",
]

CXX = "g++"

if platform.system() == "Windows":
    CXX = "clang++.exe"
    STANC = STANC.with_suffix('.exe')
    CPP_DEFINES.extend(["_BOOST_LGAMMA", "TBB_INTERFACE_NEW"])
    CONDA_PATH = Path(os.environ["CONDA_PREFIX"])
    OTHER_INCLUDES.append(str(CONDA_PATH / "Library" / "include"))
    LDFLAGS = [
        f'-Wl",/LIBPATH:{CONDA_PATH / "Library" / "lib"}"',
        f'-Wl",/LIBPATH:{CONDA_PATH / "libs"}"',
    ]
else:  # unix
    CXX_FLAGS.extend(["-fPIC", "-fvisibility=hidden"])
    LIBRARIES.append("m")
    LDFLAGS = [
        f'-Wl,-L,"{CMDSTAN}/stan/lib/stan_math/lib/tbb"',
        f'-Wl,-L,"{CMDSTAN}/stan/lib/stan_math/lib/sundials_6.1.1/lib"',
        f'-Wl,-rpath,"{CMDSTAN}/stan/lib/stan_math/lib/tbb"',
    ]
    # assume we're using the vendored sundials/tbb, could be extended one day
    CMDSTAN_SUB_INCLUDES.extend(
        [
            ("stan", "lib", "stan_math", "lib", "tbb_2020.3", "include"),
            ("stan", "lib", "stan_math", "lib", "sundials_6.1.1", "include"),
            ("stan", "lib", "stan_math", "lib", "sundials_6.1.1", "src", "sundials"),
        ]
    )

if platform.system() == "Darwin":
    CXX = "clang++"
    CXX_FLAGS.extend(["-undefined", "dynamic_lookup"])

CMDSTAN_INCLUDE_PATHS = [str(CMDSTAN.joinpath(*sub)) for sub in CMDSTAN_SUB_INCLUDES]


CPP_FLAGS = [f"-D{define}" for define in CPP_DEFINES] + [
    f"-I{path}"
    for path in CMDSTAN_INCLUDE_PATHS + OTHER_INCLUDES + get_pybind_includes()
]
EXT_SUFFIX = dist_sysconfig.get_config_var("EXT_SUFFIX")
LDLIBS = [f"-l{lib}" for lib in LIBRARIES]


def expose(file: str):
    file_path = Path(file).resolve()
    subprocess.run(
        [
            str(STANC),
            "--standalone-functions",
            f"--include-paths={file_path.parent}",
            f"--o={file_path.parent / file_path.stem}.cpp-pre",
            str(file_path),
        ],
        check=True,
    )
    preprocess.preprocess(
        str(file_path.parent / file_path.stem) + ".cpp-pre",
        out=(str(file_path.parent / file_path.stem) + ".cpp"),
    )
    CMD = (
        [CXX]
        + CXX_FLAGS
        + CPP_FLAGS
        + [
            f"-o{file_path.parent / file_path.stem}{EXT_SUFFIX}",
            f"{file_path.parent / file_path.stem}.cpp",
        ]
        + LDFLAGS
        + LDLIBS
    )

    res = subprocess.run(
        " ".join(CMD),  # TODO investigate if can use shell=False
        shell=True,
        check=False,
        capture_output=True,
        text=True,
    )

    if res.returncode:
        raise RuntimeError("Build failed!\n" + res.stderr)
    sys.path.append(str(file_path.parent))
    
    return importlib.import_module(file_path.stem)
