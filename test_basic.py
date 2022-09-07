import numpy as np
from contextlib import redirect_stdout
import io

import sys, os
sys.path.append(os.getcwd() + "/..")

import basic

print(basic.int_only_multiplication(4,5))

print(basic.my_vector_mul_by_5(np.arange(1,10)))

print(basic.array_fun([1,2,3,4,5.5]))

print(basic.test_rng(10, base_rng=basic.StanRNG(123)))
assert basic.test_rng(10, base_rng=basic.StanRNG(123)) == basic.test_rng(10, base_rng=basic.StanRNG(123))
assert basic.test_rng(10, base_rng=basic.StanRNG(123)) != basic.test_rng(10, base_rng=basic.StanRNG(465))

basic.test_printing()

redirected = io.StringIO()
with redirect_stdout(redirected):
    basic.test_printing()

assert redirected.getvalue() == "hi there!\n"
