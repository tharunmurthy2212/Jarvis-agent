import ast
import math
import operator
from typing import Any, Dict


class SafeCalculator:
    """Evaluates mathematical expressions safely using Python's AST parser without eval/exec."""

    # Allowed unary and binary operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # Allowed safe mathematical functions and constants
    SAFE_NAMES: Dict[str, Any] = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "ceil": math.ceil,
        "floor": math.floor,
        "factorial": lambda n: math.factorial(int(min(max(0, n), 100))),  # cap to 100!
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
    }

    @classmethod
    def evaluate(cls, expression: str) -> Dict[str, Any]:
        """Safely parse and evaluate a mathematical expression."""
        if not expression or not isinstance(expression, str):
            return {"error": "Expression must be a non-empty string."}

        cleaned = expression.strip().replace("^", "**")
        if len(cleaned) > 200:
            return {"error": "Expression exceeds maximum length of 200 characters."}

        try:
            parsed = ast.parse(cleaned, mode="eval")
            result = cls._eval_node(parsed.body)
            # Format cleanly
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            elif isinstance(result, float):
                result = round(result, 8)
            return {"expression": expression, "result": result}
        except ZeroDivisionError:
            return {"error": "Division by zero is undefined."}
        except (ValueError, OverflowError) as e:
            return {"error": f"Math error: {str(e)}"}
        except Exception as e:
            return {"error": f"Invalid or disallowed mathematical expression: {str(e)}"}

    @classmethod
    def _eval_node(cls, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numeric constants are allowed.")

        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type in cls.OPERATORS:
                return cls.OPERATORS[op_type](cls._eval_node(node.operand))
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")

        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type in cls.OPERATORS:
                left = cls._eval_node(node.left)
                right = cls._eval_node(node.right)
                # Safeguard against huge exponents
                if op_type is ast.Pow:
                    if abs(right) > 1000:
                        raise OverflowError("Exponent too large (max 1000).")
                return cls.OPERATORS[op_type](left, right)
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in cls.SAFE_NAMES:
                    func = cls.SAFE_NAMES[func_name]
                    args = [cls._eval_node(arg) for arg in node.args]
                    return func(*args)
            raise ValueError("Unauthorized or unknown function call.")

        elif isinstance(node, ast.Name):
            if node.id in cls.SAFE_NAMES:
                return cls.SAFE_NAMES[node.id]
            raise ValueError(f"Unknown variable or constant: {node.id}")

        raise ValueError(f"Disallowed expression syntax: {type(node).__name__}")
