"""Safe arithmetic for gate angles, shared by the editor and the QASM reader.

No eval(): the expression is parsed into an AST and only numbers, pi,
+, -, *, /, ** (bounded) and parentheses are accepted. Input length and
nesting depth are capped so a crafted file cannot freeze the application.
"""
import ast
import math
import operator

MAX_EXPRESSION_LENGTH = 200
MAX_DEPTH = 32
_OP = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def parse_angle(text):
    """Evaluate an angle expression in radians, e.g. 'pi/2', '-3*pi/4', '2^3'."""
    if not isinstance(text, str):
        raise ValueError('Enter a valid angle, e.g. pi/2')
    source = text.strip().replace('π', 'pi').replace('^', '**')
    if not source:
        raise ValueError('Enter a valid angle, e.g. pi/2')
    if len(source) > MAX_EXPRESSION_LENGTH:
        raise ValueError(f'Angle expression longer than {MAX_EXPRESSION_LENGTH} characters')
    try:
        tree = ast.parse(source, mode='eval')
    except (SyntaxError, ValueError, MemoryError, RecursionError) as exc:
        raise ValueError('Enter a valid angle, e.g. pi/2') from exc

    def parse(node, depth):
        if depth > MAX_DEPTH:
            raise ValueError('Angle expression nested too deeply')
        if isinstance(node, ast.Expression):
            return parse(node.body, depth + 1)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id == 'pi':
            return math.pi
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            v = parse(node.operand, depth + 1)
            return v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp) and type(node.op) in _OP:
            return _OP[type(node.op)](parse(node.left, depth + 1), parse(node.right, depth + 1))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            base = parse(node.left, depth + 1)
            exp = parse(node.right, depth + 1)
            if abs(exp) > 12 or abs(base) > 1e6:
                raise ValueError('Angle expression too large')
            return base ** exp
        raise ValueError('Only numbers, pi, +, -, *, /, ** and parentheses are allowed')

    try:
        value = parse(tree, 0)
        if isinstance(value, complex):
            raise ValueError('Angle must be a real number')
        value = float(value)
    except (OverflowError, ZeroDivisionError, TypeError) as exc:
        raise ValueError('Invalid or unbounded angle') from exc
    if not math.isfinite(value) or abs(value) > 1e9:
        raise ValueError('Angle must be finite and reasonable')
    return value
