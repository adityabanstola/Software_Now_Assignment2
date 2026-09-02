"""
evaluator.py
------------
HIT137 Assignment 2 - Question 2

A recursive-descent expression evaluator built entirely from plain
functions (no classes). Reads one expression per line from an input file,
tokenises it, builds a parse tree, evaluates it, and writes a formatted
report to "output.txt" in the same directory as the input file.

Grammar (lowest to highest binding power)
------------------------------------------
    expression   := term (("+" | "-") term)*
    term         := unary (("*" | "/" | "%") unary | implicit_mult)*
    implicit_mult:= "(" expression ")"          # juxtaposition -> "*"
    unary        := "-" unary | power
    power        := primary ("^" unary)?        # right associative
    primary      := NUMBER | "(" expression ")"

Two adjacent number literals with nothing between them (e.g. "2 3") are
NOT implicit multiplication -- they are simply invalid and produce a
parse error, since after parsing "2" as a complete expression the
leftover "3" token cannot be consumed.
"""

from __future__ import annotations

import os


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_SINGLE_CHAR_OPS = set("+-*/%^")


def tokenize(text: str):
    """Turn an expression string into a list of (type, value) tuples.

    Returns None if the text contains an invalid/unrecognised character.
    Token types: 'NUM', 'OP', 'LPAREN', 'RPAREN', 'END'.
    """
    tokens = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        if ch.isspace():
            i += 1
            continue

        if ch.isdigit():
            start = i
            while i < n and text[i].isdigit():
                i += 1
            if i < n and text[i] == ".":
                i += 1
                if i >= n or not text[i].isdigit():
                    return None  # malformed number like "3."
                while i < n and text[i].isdigit():
                    i += 1
            tokens.append(("NUM", text[start:i]))
            continue

        if ch in _SINGLE_CHAR_OPS:
            tokens.append(("OP", ch))
            i += 1
            continue

        if ch == "(":
            tokens.append(("LPAREN", "("))
            i += 1
            continue

        if ch == ")":
            tokens.append(("RPAREN", ")"))
            i += 1
            continue

        # Unrecognised character -> whole tokenisation fails
        return None

    tokens.append(("END", ""))
    return tokens


def format_tokens(tokens) -> str:
    """Render a token list in the "[TYPE:value] [TYPE:value] ... [END]" form."""
    parts = []
    for ttype, value in tokens:
        if ttype == "END":
            parts.append("[END]")
        else:
            parts.append(f"[{ttype}:{value}]")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Parser (recursive descent) -> builds a simple tuple-based parse tree
#
#   number         -> ("num", "3")
#   binary op       -> ("bin", "+", left, right)
#   unary negation  -> ("neg", operand)
# ---------------------------------------------------------------------------

class _ParseError(Exception):
    pass


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _peek(self):
        return self.tokens[self.pos]

    def _advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, ttype):
        tok = self._peek()
        if tok[0] != ttype:
            raise _ParseError(f"Expected {ttype} but found {tok}")
        return self._advance()

    # expression := term (("+"|"-") term)*
    def parse_expression(self):
        node = self.parse_term()
        while self._peek()[0] == "OP" and self._peek()[1] in ("+", "-"):
            op = self._advance()[1]
            right = self.parse_term()
            node = ("bin", op, node, right)
        return node

    # term := unary (("*"|"/"|"%") unary | implicit-"(" expression ")")*
    def parse_term(self):
        node = self.parse_unary()
        while True:
            ttype, tvalue = self._peek()
            if ttype == "OP" and tvalue in ("*", "/", "%"):
                self._advance()
                right = self.parse_unary()
                node = ("bin", tvalue, node, right)
            elif ttype == "LPAREN":
                # implicit multiplication: <factor> "(" ... ")"
                right = self.parse_unary()
                node = ("bin", "*", node, right)
            else:
                break
        return node

    # unary := "-" unary | power
    def parse_unary(self):
        ttype, tvalue = self._peek()
        if ttype == "OP" and tvalue == "-":
            self._advance()
            operand = self.parse_unary()
            return ("neg", operand)
        if ttype == "OP" and tvalue == "+":
            raise _ParseError("Unary '+' is not supported")
        return self.parse_power()

    # power := primary ("^" unary)?      (right associative)
    def parse_power(self):
        base = self.parse_primary()
        ttype, tvalue = self._peek()
        if ttype == "OP" and tvalue == "^":
            self._advance()
            exponent = self.parse_unary()
            return ("bin", "^", base, exponent)
        return base

    # primary := NUM | "(" expression ")"
    def parse_primary(self):
        ttype, tvalue = self._peek()
        if ttype == "NUM":
            self._advance()
            return ("num", tvalue)
        if ttype == "LPAREN":
            self._advance()
            node = self.parse_expression()
            self._expect("RPAREN")
            return node
        raise _ParseError(f"Unexpected token {(ttype, tvalue)}")


def parse(tokens):
    """Parse a full token list into a tree. Raises _ParseError on failure."""
    parser = _Parser(tokens)
    tree = parser.parse_expression()
    if parser._peek()[0] != "END":
        raise _ParseError(f"Unexpected trailing token {parser._peek()}")
    return tree


# ---------------------------------------------------------------------------
# Tree -> string formatting
# ---------------------------------------------------------------------------

def format_number(text: str) -> str:
    """Format a raw numeric literal the way it should appear in the tree:
    integers with no trailing '.0', decimals kept as typed."""
    value = float(text)
    if value == int(value):
        return str(int(value))
    return text


def format_tree(node) -> str:
    kind = node[0]
    if kind == "num":
        return format_number(node[1])
    if kind == "neg":
        return f"(neg {format_tree(node[1])})"
    if kind == "bin":
        _, op, left, right = node
        return f"({op} {format_tree(left)} {format_tree(right)})"
    raise ValueError(f"Unknown node kind: {kind}")


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class _EvalError(Exception):
    pass


def evaluate_tree(node) -> float:
    kind = node[0]
    if kind == "num":
        return float(node[1])
    if kind == "neg":
        return -evaluate_tree(node[1])
    if kind == "bin":
        _, op, left, right = node
        lval = evaluate_tree(left)
        rval = evaluate_tree(right)
        if op == "+":
            return lval + rval
        if op == "-":
            return lval - rval
        if op == "*":
            return lval * rval
        if op == "/":
            if rval == 0:
                raise _EvalError("Division by zero")
            return lval / rval
        if op == "%":
            if rval == 0:
                raise _EvalError("Modulo by zero")
            return lval % rval
        if op == "^":
            return lval ** rval
        raise _EvalError(f"Unknown operator: {op}")
    raise _EvalError(f"Unknown node kind: {kind}")


def format_result(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{round(value, 4)}"


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def evaluate_expression(expr: str) -> dict:
    """Evaluate a single expression string and return its result dict."""
    tokens = tokenize(expr)
    if tokens is None:
        return {"input": expr, "tree": "ERROR", "tokens": "ERROR", "result": "ERROR"}

    tokens_str = format_tokens(tokens)

    try:
        tree = parse(tokens)
    except _ParseError:
        return {"input": expr, "tree": "ERROR", "tokens": tokens_str, "result": "ERROR"}

    tree_str = format_tree(tree)

    try:
        value = evaluate_tree(tree)
    except _EvalError:
        return {"input": expr, "tree": tree_str, "tokens": tokens_str, "result": "ERROR"}

    return {
        "input": expr,
        "tree": tree_str,
        "tokens": tokens_str,
        "result": float(value),
    }


def evaluate_file(input_path: str) -> list:
    """Read expressions (one per line) from input_path, evaluate each, write
    output.txt to the same directory, and return the list of result dicts."""
    with open(input_path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n").rstrip("\r") for line in f]

    # Ignore fully blank trailing lines, but keep interior blank lines out
    # of the expression list (an expression file has one expression/line).
    expressions = [line for line in lines if line.strip() != ""]

    results = [evaluate_expression(expr) for expr in expressions]

    output_path = os.path.join(os.path.dirname(os.path.abspath(input_path)), "output.txt")
    _write_output(results, output_path)

    return results


def _write_output(results: list, output_path: str) -> None:
    blocks = []
    for r in results:
        result_line = r["result"] if r["result"] == "ERROR" else format_result(r["result"])
        block = (
            f"Input: {r['input']}\n"
            f"Tree: {r['tree']}\n"
            f"Tokens: {r['tokens']}\n"
            f"Result: {result_line}"
        )
        blocks.append(block)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(blocks) + "\n")


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "input.txt"
    evaluate_file(path)
    print(f"Done. Results written to output.txt (next to '{path}').")
