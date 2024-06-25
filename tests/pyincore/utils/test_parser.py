from pyincore import Parser
from pyincore.utils import evaluateexpression
import pytest


def test_evaluator():
    invalid_expression = "__import__('subprocess').getoutput('mkdir invalid')"

    with pytest.raises(NameError):
        evaluateexpression.evaluate(invalid_expression)


def test_loop():
    loop_string = 'for x in range(10):\n  print("haha!")'
    invalid_expression = "exec(x)"

    with pytest.raises(NameError):
        evaluateexpression.evaluate(invalid_expression, {"x": loop_string})


def test_exec_evaluator():
    program = 'a = 5\nb=10\nprint("Sum =", a+b)'
    with pytest.raises(NameError):
        evaluateexpression.evaluate("exec(program)", {"program": program})


def test_exec_evaluator_repair():
    expression = "scipy.stats.lognorm.ppf(numpy.random.random(size=rand_arr_size), s=0.159, scale=numpy.exp(0.8196))"
    r = evaluateexpression.evaluate(expression, {"rand_arr_size": 10})
    assert len(r) == 10


def test_parser():
    parser = Parser()

    result = parser.parse("x^2").evaluate({'x': 4})
    assert result == 16

    variable = parser.parse("log(x)*3").variables()
    assert variable == ['x']

    assert parser.parse("pow(x,y)").variables() == ['x', 'y']

    assert parser.parse("1").evaluate({}) == 1

    assert parser.parse('a').evaluate({'a': 2}) == 2

    assert parser.parse("(a**2-b**2)==((a+b)*(a-b))").evaluate({'a': 4859, 'b': 13150}) is True

    assert parser.parse('log(16,2)').evaluate({}) == 4.0

    assert parser.parse("x^2").variables() == ['x']
