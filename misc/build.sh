#!/bin/bash

model_name=$(basename "$1" .stan)

echo "Compiling $1 to C++"
$CMDSTAN/bin/stanc --standalone-functions --o="$model_name".cpp "$1"
echo "Injecting PyBind11 specific code"
python ./src/preprocess.py "$model_name".cpp
echo "Compiling to shared object"
if [ "$(uname -s)" == "Darwin" ]; then
    extra_args="-undefined dynamic_lookup"
    dll_ext=".dylib"
else
    extra_args=""
    dll_ext=".so.2"
fi
g++ -std=c++17 $extra_args -O3 -D_REENTRANT -DBOOST_DISABLE_ASSERTS -Wno-sign-compare -Wno-ignored-attributes -I "$CMDSTAN"/stan/lib/stan_math/lib/tbb_2020.3/include  -I "$CMDSTAN"/stan/src -I "$CMDSTAN"/lib/rapidjson_1.1.0/ -I "$CMDSTAN"/stan/lib/stan_math/ -I "$CMDSTAN"/stan/lib/stan_math/lib/eigen_3.4.0 -I "$CMDSTAN"/stan/lib/stan_math/lib/boost_1.84.0 -I "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/include -I $CMDSTAN/stan/lib/stan_math/lib/sundials_6.1.1/src/sundials $(python3 -m pybind11 --includes) -shared -fPIC "$model_name".cpp -o "$model_name$(python3-config --extension-suffix)" -Wl,-L,"$CMDSTAN/stan/lib/stan_math/lib/tbb" -Wl,-rpath,"$CMDSTAN/stan/lib/stan_math/lib/tbb" "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_nvecserial.a "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_cvodes.a "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_idas.a "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_kinsol.a "$CMDSTAN"/stan/lib/stan_math/lib/tbb/libtbb"$dll_ext"
