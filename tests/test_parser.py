from pyincore import Parser


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




