import os
import re
import sys

INCLUDES = """

#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>
#include <pybind11/iostream.h>
namespace py = pybind11;

"""


def insert_includes(text):
    i = text.find("namespace")
    return text[:i] + INCLUDES + text[i:]


BOILERPLATE = """
PYBIND11_MODULE({model_name}, m)
{{

  py::class_<stan::rng_t>(m, "StanRNG")
      .def(py::init<int>());

  using acc = stan::math::accumulator<double>;
  py::class_<acc>(m, "StanAccumulator")
      .def(py::init())
      .def("sum", &acc::sum);

  m.doc() = "{model_name}.stan functions";

  {functions}
}}
"""


REDIRECT = "py::call_guard<py::scoped_ostream_redirect, py::scoped_estream_redirect>()"


def py_arg(name, default=None):
    if default:
        return f'py::arg("{name}") = {default}'
    return f'py::arg("{name}")'


def py_fun(fn, is_overload):
    name, args_defaults = fn
    args = ", ".join(py_arg(name, default) for (name, _, default) in args_defaults)
    if is_overload:
        arg_tys = [ty for (_, ty, _) in args_defaults]
        fn_ptr = f"py::overload_cast<{', '.join(arg_tys)}>(&{name})"
    else:
        fn_ptr = f"&{name}"
    return f'm.def("{name}", {fn_ptr}, {args}{", " if args else ""}{REDIRECT});'


# extract information from functions
arg_matcher = re.compile(
    r"([a-zA-Z][a-zA-Z0-9,&*:\-_<>\s=]*)\s+([a-zA-Z0-9_\-]+)\(([a-zA-Z0-9,&*:\-_<>\s=\n]*)\)"
)


def munge_args(args: str):
    flattened = args.replace("\n", "").replace("\r", "")
    args_split = []
    arg = ""
    inside_template = 0
    for c in flattened:
        if c == "<":
            inside_template += 1
        elif c == ">":
            inside_template -= 1
        elif c == "," and inside_template == 0:
            args_split.append(arg.strip())
            arg = ""
            continue
        arg += c

    if arg:
        args_split.append(arg.strip())

    return args_split


def populate_boilerplate(model_name, text):
    functions_text = text.split("// [[stan::function]]\n")[1:]
    functions: list[tuple[str, list[tuple[str, str]]]] = []

    seen_functions = set()
    overloaded_functions = set()
    for fn in functions_text:
        match = arg_matcher.match(fn)
        name = match[2]
        if name in seen_functions:
            overloaded_functions.add(name)
        seen_functions.add(name)
        args = munge_args(match[3])

        arg_tys = []
        arg_names = []
        arg_defaults = []
        for arg in args:
            arg_ty, arg_name = arg.rsplit(" ", maxsplit=1)
            arg_ty += "&" * arg_name.count("&")
            arg_names.append(arg_name.replace("&", "").replace("__", ""))
            arg_tys.append(arg_ty)

            if arg.startswith("stan::rng_t"):
                arg_defaults.append("stan::rng_t(1234)")
            else:
                arg_defaults.append("")

        functions.append((name, list(zip(arg_names, arg_tys, arg_defaults))))

    function_defs = "\n  ".join(
        py_fun(f, f[0] in overloaded_functions) for f in functions
    )

    return BOILERPLATE.format(model_name=model_name, functions=function_defs)


# edit function code
ostream_matcher = re.compile(
    r"(,(\s|\n)+)?std::ostream\*(\s|\n)+pstream__(\s|\n)+=(\s|\n)+nullptr"
)


def set_cout(text):
    i = text.find("// [[stan::function]")
    preamble = text[:i]
    funs = text[i:]
    stripped_arg = ostream_matcher.subn("", funs)[0]
    couts = stripped_arg.replace("pstream__", "&std::cout")
    return preamble + couts


def preprocess(file, out=None):
    if out is None:
        out = file

    model, _ = os.path.splitext(os.path.basename(file))

    with open(file, "r") as f:
        text = f.read()

    if "// [[stan::function]" not in text:
        raise ValueError(
            "C++ file has no stan functions exposed. Did you forget --standalone-functions?"
        )

    text = set_cout(insert_includes(text))
    text += populate_boilerplate(model, text)

    with open(out, "w") as f:
        f.write(text)


if __name__ == "__main__":
    file = sys.argv[1]
    preprocess(file)
