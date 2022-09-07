# Exposing Stan functions in Python through PyBind11

This repo contains (a very work in progress attempt at) code to expose functions
written in a Stan model to the Python runtime through the
[PyBind11](https://pybind11.readthedocs.io/en/stable/) library.

This is very similar to *[Exposing Stan user-defined functions using CmdStanR and Rcpp](https://rok-cesnovar.github.io/misc/exposing_cmdstanr_udf.html)*.

## Running

Currently, this has only been confirmed to work on Ubuntu. It assumes you have a working installation of
[CmdStan](https://github.com/stan-dev/cmdstan), and a Python environment with both
[cmdstanpy](https://github.com/stan-dev/cmdstanpy) and [PyBind11](https://github.com/pybind/pybind11)

```shell
./build.sh basic.stan
python test_basic.stan
```

Alternatively, from inside python
```python
import expose_stan_functions
basic = expose_stan_functions.expose('basic.stan')
basic.test_printing() # etc
```
