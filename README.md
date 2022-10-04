# Exposing Stan functions in Python through PyBind11

This repo contains (a very work in progress attempt at) code to expose functions
written in a Stan model to the Python runtime through the
[PyBind11](https://pybind11.readthedocs.io/en/stable/) library.

This is very similar to *[Exposing Stan user-defined functions using CmdStanR and Rcpp](https://rok-cesnovar.github.io/misc/exposing_cmdstanr_udf.html)*.

This supports all possible Stan functions, including pRNGs and functions which edit the `target` variable.
These are supported through two objects exposed on all models, `StanRNG` and `StanAccumulator`, which are
thin wrappers for `boost::ecuyer1988` and `stan::math::accumulator<double>`, respectively.

## Running

Currently, this has only been confirmed to work on Ubuntu. It assumes you have a working installation of
[CmdStan](https://github.com/stan-dev/cmdstan), and a Python environment with both
[cmdstanpy](https://github.com/stan-dev/cmdstanpy) and [PyBind11](https://github.com/pybind/pybind11)

```python
import pybind_stan_fns
basic = pybind_stan_fns.expose('./test/basic.stan')
basic.test_printing() # etc
```

### Errata

There is a pure-shell version of this which just runs `g++` directly.

```shell
./build.sh basic.stan
python test_basic.stan
```

There is also an experiment using `setuptools` to build the module in `setuptools_version.py`.
This probably has the brightest future in terms of working on other platforms.
