import importlib
import preprocess
import subprocess
import cmdstanpy
from pathlib import Path
import os

stanc = Path(cmdstanpy.cmdstan_path()) / "bin" / ("stanc"+cmdstanpy.utils.EXTENSION)

def expose(file: str):
    model, _ = os.path.splitext(os.path.basename(file))
    file_path = Path(file)
    subprocess.run([str(stanc), f"--o={file_path.stem}.cpp-pre", file], check=True)
    preprocess.preprocess(file_path.stem+".cpp-pre", out=file_path.stem+".cpp")
    subprocess.run([f'g++ -std=c++1y -D_REENTRANT -Wno-sign-compare -Wno-ignored-attributes -I "$CMDSTAN"/stan/lib/stan_math/lib/tbb_2020.3/include -O3 -I "$CMDSTAN"/stan/src -I "$CMDSTAN"/lib/rapidjson_1.1.0/ -I "$CMDSTAN"/stan/lib/stan_math/ -I "$CMDSTAN"/stan/lib/stan_math/lib/eigen_3.3.9 -I "$CMDSTAN"/stan/lib/stan_math/lib/boost_1.78.0 -I "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/include -I $CMDSTAN/stan/lib/stan_math/lib/sundials_6.1.1/src/sundials-DBOOST_DISABLE_ASSERTS $(python3 -m pybind11 --includes) -shared -lm -fPIC {file_path.stem}.cpp -o "{file_path.stem}$(python3-config --extension-suffix)" -Wl,-L,"$CMDSTAN/stan/lib/stan_math/lib/tbb" -Wl,-rpath,"$CMDSTAN/stan/lib/stan_math/lib/tbb" -lpthread -Wl,-L,"$CMDSTAN/stan/lib/stan_math/lib/tbb" -Wl,-rpath,"$CMDSTAN/stan/lib/stan_math/lib/tbb" "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_nvecserial.a "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_cvodes.a "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_idas.a "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_kinsol.a "$CMDSTAN"/stan/lib/stan_math/lib/tbb/libtbb.so.2'],
                    shell=True, check=True)
    return importlib.import_module(model)

