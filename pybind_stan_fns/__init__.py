import importlib
import os
import platform
import shlex
import subprocess
import sys
import sysconfig
from pathlib import Path

import cmdstanpy
import pybind11

from . import preprocess


# ---------------------------------------------------------------------------
# Basic configuration
# ---------------------------------------------------------------------------

SYSTEM = platform.system()
CMDSTAN = Path(cmdstanpy.cmdstan_path())
STANC = CMDSTAN / "bin" / "stanc"
if SYSTEM == "Windows":
    STANC = STANC.with_suffix(".exe")

STAN_MATH = CMDSTAN / "stan" / "lib" / "stan_math"
STAN_LIB = STAN_MATH / "lib"
TBB_DIR = STAN_LIB / "tbb"
SUNDIALS_DIR = STAN_LIB / "sundials_6.1.1"
SUNDIALS_LIB = SUNDIALS_DIR / "lib"

CPP_DEFINES = ["_REENTRANT", "BOOST_DISABLE_ASSERTS"]
LIBRARIES = ["sundials_nvecserial", "sundials_cvodes",
             "sundials_idas", "sundials_kinsol"]

CXX_FLAGS = [
    "-std=c++17", "-O3",
    "-Wno-sign-compare",
    "-Wno-deprecated-builtins",
    "-Wno-ignored-attributes",
]

INCLUDE_PARTS = [
    ("stan", "src"),
    ("stan", "lib", "rapidjson_1.1.0"),
    ("stan", "lib", "stan_math"),
    ("stan", "lib", "stan_math", "lib", "eigen_3.4.0"),
    ("stan", "lib", "stan_math", "lib", "boost_1.87.0"),
]

LDFLAGS = []
LDLIBS = []
EXTRA_INCLUDES = []


def pybind_includes():
    """Return unique Python/pybind11 include directories."""
    paths = [
        sysconfig.get_path("include"),
        sysconfig.get_path("platinclude"),
        pybind11.get_include(),
    ]
    return list(dict.fromkeys(p for p in paths if p))


def find_python_library(conda_path):
    """Find the import library for the running Python on Windows."""
    version = sysconfig.get_python_version().replace(".", "")
    search = []

    if libdir := sysconfig.get_config_var("LIBDIR"):
        search.append(Path(libdir))
    search.append(conda_path / "libs")

    for directory in search:
        exact = directory / f"python{version}.lib"
        if exact.exists():
            return exact

        candidates = sorted(directory.glob("python*.lib"))
        if candidates:
            return candidates[0]

    raise RuntimeError(
        "Could not find Python import library.\n"
        f"Python: {sys.executable}\n"
        f"Version: {sys.version}\n"
        f"Searched: {search}"
    )


# ---------------------------------------------------------------------------
# Platform-specific configuration
# ---------------------------------------------------------------------------

if SYSTEM == "Windows":
    CXX = "clang++.exe"

    CPP_DEFINES += ["_BOOST_LGAMMA", "TBB_INTERFACE_NEW"]
    CXX_FLAGS += ["-shared"]

    conda = os.environ.get("CONDA_PREFIX")
    if not conda:
        raise RuntimeError("CONDA_PREFIX is not set.")

    CONDA_PATH = Path(conda)
    CONDA_INCLUDE = CONDA_PATH / "Library" / "include"
    CONDA_LIB = CONDA_PATH / "Library" / "lib"

    EXTRA_INCLUDES.append(os.fspath(CONDA_INCLUDE))

    python_lib = find_python_library(CONDA_PATH)

    LDFLAGS += [
        f"-L{python_lib.parent}",
        f"-L{CONDA_LIB}",
        f"-L{SUNDIALS_LIB}",
    ]
    LDLIBS += [
        os.fspath(python_lib),
        "-ltbb",
        *(f"-l{x}" for x in LIBRARIES),
    ]

elif SYSTEM in {"Linux", "Darwin"}:
    CXX = "g++" if SYSTEM == "Linux" else "clang++"

    CXX_FLAGS += [
        "-fPIC",
        "-fvisibility=hidden",
        "-shared" if SYSTEM == "Linux" else "-dynamiclib",
    ]

    if SYSTEM == "Darwin":
        CXX_FLAGS += ["-undefined", "dynamic_lookup"]

    INCLUDE_PARTS += [
        ("stan", "lib", "stan_math", "lib", "tbb_2020.3", "include"),
        ("stan", "lib", "stan_math", "lib", "sundials_6.1.1", "include"),
        ("stan", "lib", "stan_math", "lib", "sundials_6.1.1",
         "src", "sundials"),
    ]

    LDFLAGS += [
        f"-L{TBB_DIR}",
        f"-L{SUNDIALS_LIB}",
        f"-Wl,-rpath,{TBB_DIR}",
        f"-Wl,-rpath,{SUNDIALS_LIB}",
    ]

    tbb = TBB_DIR / ("libtbb.dylib" if SYSTEM == "Darwin" else "libtbb.so.2")
    if not tbb.exists():
        raise RuntimeError(f"Could not find vendored TBB library: {tbb}")

    LDLIBS += [os.fspath(tbb), *(f"-l{x}" for x in LIBRARIES)]

else:
    raise RuntimeError(f"Unsupported operating system: {SYSTEM}")


# ---------------------------------------------------------------------------
# Compiler flags
# ---------------------------------------------------------------------------

INCLUDE_PATHS = [
    os.fspath(CMDSTAN.joinpath(*parts))
    for parts in INCLUDE_PARTS
]

CPP_FLAGS = (
    [f"-D{x}" for x in CPP_DEFINES]
    + [f"-I{x}" for x in INCLUDE_PATHS + EXTRA_INCLUDES + pybind_includes()]
)

EXT_SUFFIX = sysconfig.get_config_var("EXT_SUFFIX")
if not EXT_SUFFIX:
    raise RuntimeError("Could not determine Python extension suffix.")


def _print_config():
    print(
        "\n========== pybind_stan_fns build configuration ==========\n"
        f"Platform:          {SYSTEM}\n"
        f"Architecture:      {platform.machine()}\n"
        f"Python:            {sys.executable}\n"
        f"Python version:    {platform.python_version()}\n"
        f"Compiler:          {CXX}\n"
        f"CmdStan:           {CMDSTAN}\n"
        f"TBB directory:     {TBB_DIR}\n"
        f"Extension suffix:  {EXT_SUFFIX}\n"
        + (
            f"Python library:    {python_lib}\n"
            if SYSTEM == "Windows"
            else ""
        )
        + "==========================================================\n"
    )


def expose(file: str):
    """Compile a Stan file into a Python extension module."""
    path = Path(file).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Stan file does not exist: {path}")

    cpp_pre = path.with_suffix(".cpp-pre")
    cpp_file = path.with_suffix(".cpp")
    extension = path.with_suffix(EXT_SUFFIX)

    subprocess.run([
        os.fspath(STANC),
        "--standalone-functions",
        f"--include-paths={path.parent}",
        f"--o={cpp_pre}",
        os.fspath(path),
    ], check=True)

    preprocess.preprocess(os.fspath(cpp_pre), out=os.fspath(cpp_file))

    command = (
        [CXX] + CXX_FLAGS + CPP_FLAGS +
        ["-o", os.fspath(extension), os.fspath(cpp_file)] +
        LDFLAGS + LDLIBS
    )

    print("\nBuild command:")
    print(" ".join(shlex.quote(str(x)) for x in command))

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode:
        _print_config()
        raise RuntimeError(
            "Build failed!\n\n"
            f"Command:\n{' '.join(shlex.quote(str(x)) for x in command)}\n\n"
            f"stdout:\n{result.stdout}\n\n"
            f"stderr:\n{result.stderr}"
        )

    module_dir = os.fspath(path.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    return importlib.import_module(path.stem)
