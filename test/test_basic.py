import io
import os
import sys
from contextlib import redirect_stdout
from glob import glob
from pathlib import Path

import numpy as np
import pytest

from pybind_stan_fns import expose

HERE = Path(__file__).parent.resolve()

try:
    import pybind11  # noqa
except ImportError:
    pytest.skip("PyBind11 not installed!", allow_module_level=True)

if sys.platform.startswith("win"):
    pytest.skip("Exposed function tests cannot run on Windows", allow_module_level=True)


@pytest.fixture(scope="session")
def basic():
    module = expose(HERE / "basic.stan")
    yield module
    for file in glob("./basic.*"):
        if not file.endswith(".stan"):
            os.remove(file)


def test_simple_functions(basic):
    assert basic.int_only_multiplication(4,5) == 20
    np.testing.assert_array_equal(basic.my_vector_mul_by_5(np.arange(1,10)), np.arange(1,10) * 5)

    assert basic.array_fun([1,2,3,4,5.5]) == sum([1,2,3,4,5.5])

def test_rng(basic):
    assert basic.test_rng(10, base_rng=basic.StanRNG(123)) == basic.test_rng(10, base_rng=basic.StanRNG(123))
    assert basic.test_rng(10, base_rng=basic.StanRNG(123)) != basic.test_rng(10, base_rng=basic.StanRNG(465))


def test_printing(basic):
    basic.test_printing()
    redirected = io.StringIO()
    with redirect_stdout(redirected):
        basic.test_printing()

    assert redirected.getvalue() == "hi there!\n"

def test_error(basic):
    with pytest.raises(ValueError):
        basic.test_error()


def test_overload(basic):
    assert basic.test_overload() == 0
    assert basic.test_overload(34) == 1
    assert basic.test_overload(np.arange(2,4)) == 2
