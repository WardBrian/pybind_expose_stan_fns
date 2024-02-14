# Exposing Stan functions in Python through PyBind11

This repo contains (a very work in progress attempt at) code to expose functions
written in a Stan model to the Python runtime through the
[PyBind11](https://pybind11.readthedocs.io/en/stable/) library.

This is very similar to *[Exposing Stan user-defined functions using CmdStanR and Rcpp](https://rok-cesnovar.github.io/misc/exposing_cmdstanr_udf.html)*.

This supports all possible Stan functions, including pRNGs and functions which edit the `target` variable.
These are supported through two objects exposed on all models, `StanRNG` and `StanAccumulator`, which are
thin wrappers for `stan::rng_t` and `stan::math::accumulator<double>`, respectively.

## Running

This assumes you have a working installation of
[CmdStan](https://github.com/stan-dev/cmdstan), and a Python environment with both
[cmdstanpy](https://github.com/stan-dev/cmdstanpy) and [PyBind11](https://github.com/pybind/pybind11)

```python
import pybind_stan_fns
basic = pybind_stan_fns.expose('./test/basic.stan')
basic.test_printing() # etc
```

**Note**: On Windows, the above is not sufficient. One also must have
the [Microsoft Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/),
including the optional LLVM/Clang extensions, and a pre-built version of both Sundials and TBB.
The `expose` function assumes these were installed via [conda](https://docs.conda.io/en/latest/).
Our [CI Pipeline](./github/workflows/main.yaml) shows how this is done in Github Actions

### Miscellany

There is a (possibly outdated) pure-shell version of this which just runs `g++` directly.

```shell
./build.sh basic.stan
python test_basic.stan
```

Similarly on Windows, there is a `build.ps1` powershell script.

Finally, there is also a version which attempts to use `setuptools` for the same effect.
