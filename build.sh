#!/bin/bash

CMDSTAN=/home/brian/Dev/cpp/cmdstan
model_name=$(basename "$1" .stan)

echo "Compiling $1 to C++"
$CMDSTAN/bin/stanc --standalone-functions --o="$model_name".cpp "$1"
echo "Injecting PyBind11 specific code"
python ./src/preprocess.py "$model_name".cpp
echo "Compiling to shared object"
g++ -std=c++1y -D_REENTRANT -Wno-sign-compare -Wno-ignored-attributes -I "$CMDSTAN"/stan/lib/stan_math/lib/tbb_2020.3/include -O3 -I "$CMDSTAN"/stan/src -I "$CMDSTAN"/lib/rapidjson_1.1.0/ -I "$CMDSTAN"/stan/lib/stan_math/ -I "$CMDSTAN"/stan/lib/stan_math/lib/eigen_3.3.9 -I "$CMDSTAN"/stan/lib/stan_math/lib/boost_1.78.0 -I "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/include -I $CMDSTAN/stan/lib/stan_math/lib/sundials_6.1.1/src/sundials-DBOOST_DISABLE_ASSERTS $(python3 -m pybind11 --includes) -shared -lm -fPIC "$model_name".cpp -o "$model_name$(python3-config --extension-suffix)" -Wl,-L,"$CMDSTAN/stan/lib/stan_math/lib/tbb" -Wl,-rpath,"$CMDSTAN/stan/lib/stan_math/lib/tbb" -lpthread -Wl,-L,"$CMDSTAN/stan/lib/stan_math/lib/tbb" -Wl,-rpath,"$CMDSTAN/stan/lib/stan_math/lib/tbb" "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_nvecserial.a "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_cvodes.a "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_idas.a "$CMDSTAN"/stan/lib/stan_math/lib/sundials_6.1.1/lib/libsundials_kinsol.a "$CMDSTAN"/stan/lib/stan_math/lib/tbb/libtbb.so.2
