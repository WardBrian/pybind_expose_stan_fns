# ASSUMES:
# 1. MSVC build tools and the optional Clang/LLVM extension are installed
# 2. Sundials and TBB are installed via conda
# 3. CmdStan or some other copy of the Stan sources is downloaded

$cmdstan_location = "$env:CMDSTAN"
$file = $args[0]

Invoke-Expression "$cmdstan_location\bin\stanc.exe --standalone-functions --o=$file.cpp $file.stan"
Invoke-Expression "python ./pybind_stan_fns/preprocess.py $file.cpp"

$conda_library_path = "$env:CONDA_PREFIX\Library"
$cpython_libs = "$conda_library_path\libs"

# equivalent of python3-config command on other platforms
$extension = python -c "from distutils import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))"
$pybind_includes = python -m pybind11 --includes

$cxxflags = '-std=c++1y -O3 -D_REENTRANT -DBOOST_DISABLE_ASSERTS -D_BOOST_LGAMMA -DTBB_INTERFACE_NEW -Wno-sign-compare -Wno-deprecated-builtins -Wno-ignored-attributes -shared'
$cppflags = "-I $conda_library_path\include\ -I $cmdstan_location/stan/src -I $cmdstan_location/stan/lib/rapidjson_1.1.0/ -I $cmdstan_location/stan/lib/stan_math/ -I $cmdstan_location/stan/lib/stan_math/lib/eigen_3.3.9 -I $cmdstan_location/stan/lib/stan_math/lib/boost_1.78.0 $pybind_includes"

$linkflags = "-Wl`",/LIBPATH:$conda_library_path\lib\`" -Wl`",/LIBPATH:$cpython_libs`""
$linklibs = '-ltbb -lsundials_nvecserial -lsundials_cvodes -lsundials_idas -lsundials_kinsol'

Invoke-Expression "clang++ $cppflags $cxxflags -o $file$extension $file.cpp $linkflags $linklibs"

rm "$file.*.exp"
rm "$file.*.lib"

