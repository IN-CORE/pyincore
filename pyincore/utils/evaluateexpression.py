import math
import scipy

INVALID_NAMES = ["exec", "func", "eval", "type", "isinstance", "getattr", "setattr", "repr",
                 "compile", "open"]


def evaluate(expression: str, parameters: dict = {}):
    """Evaluate a math expression."""
    # Compile the expression
    code = compile(expression, "<string>", "eval")

    # Validate allowed names
    for name in code.co_names:
        if "__" in name or name in INVALID_NAMES:
            raise NameError(f"The use of '{name}' is not allowed.")
    for parameter in parameters:
        if type(parameter) == "str" and ("__" in parameter or parameter in INVALID_NAMES):
            raise NameError(f"Using '{parameter}' is not allowed.")

    # TODO figure out a better way of doing this. Can we import the packages here directly?
    safe_globals = {"__builtins__": {}, "scipy": globals()["scipy"], "math": globals()["math"]}
    try:
        return eval(code, safe_globals, parameters)
    except ValueError:
        return math.nan
