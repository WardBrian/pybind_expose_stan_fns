# will probably only work on Unix-like systems.

import importlib
import platform
import subprocess
import sys
from pathlib import Path

import cmdstanpy

from . import preprocess

stanc = Path(cmdstanpy.cmdstan_path()) / "bin" / "stanc"


# TODO use make print-TBB_TARGETS and make print-LDFLAGS-TBB instead to support conda
if platform.system() == "Darwin":
    TBB_DLL_EXT = ".dylib"
    EXTRA_ARGS = "-undefined dynamic_lookup"
else:  # Presumed linux
    TBB_DLL_EXT = ".so.2"
    EXTRA_ARGS = ""


# TODO use cmdstan_path rather than $CMDSTAN?


def expose(file: str):
    file_path = Path(file).resolve()
    subprocess.run(
        [
            str(stanc),
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
    res = subprocess.run(
        [
            f'g++ {EXTRA_ARGS} -std=c++1y -D_REENTRANT -Wno-sign-compare -Wno-ignored-attributes -I "$CMDSTAN"/stan/lib/stan_math/lib/tbb_2020.3/include -O3 -I "$CMDSTAN"/stan/src -I "$CMDSTAN"/lib/rapidjson_1.1.0/ -I "$CMDSTAN"/stan/lib/stan_math/ -I "$CMDSTAN"/stan/lib/stan_math/lib/eigen_3.3.9 -I "$CMDSTAN"/stan/lib/stan_math/lib/boost_1.78.0 -I "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/include -I $CMDSTAN/stan/lib/stan_math/lib/sundials_6.1.1/src/sundials-DBOOST_DISABLE_ASSERTS'  # noqa
            f' $(python3 -m pybind11 --includes) -shared  -fvisibility=hidden -lm -fPIC {file_path.parent / file_path.stem}.cpp -o "{file_path.parent / file_path.stem}$(python3-config --extension-suffix)" -Wl,-L,"$CMDSTAN/stan/lib/stan_math/lib/tbb" -Wl,-rpath,"$CMDSTAN/stan/lib/stan_math/lib/tbb" -lpthread -Wl,-L,"$CMDSTAN/stan/lib/stan_math/lib/tbb" -Wl,-rpath,"$CMDSTAN/stan/lib/stan_math/lib/tbb" "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_nvecserial.a "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_cvodes.a "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_idas.a "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_kinsol.a "$CMDSTAN"/stan/lib/stan_math/lib/tbb/libtbb{TBB_DLL_EXT}'  # noqa
        ],
        shell=True,
        check=False,
        capture_output=True,
        text=True,
    )

    if res.returncode:
        raise RuntimeError("Build failed!\n" + res.stderr)
    sys.path.append(str(file_path.parent))
    return importlib.import_module(file_path.stem)
