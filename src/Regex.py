from __future__ import annotations

class Character:
    __match_args__ = ("chr",)

    def __init__(self, chr: str):
        self.chr = chr
    
    def __str__(self) -> str:
        return f"Char {self.chr}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, Character):
            return self.chr == other.chr
        return False


class Operator:
    __match_args__ = ("op",) 

    def __init__(self, op: str):
        self.op = op
        self.priority = self.priority(op)

    def __str__(self) -> str:
        return f"Op {self.op}"

    def __repr__(self):
        return str(self)
    
    def __eq__(self, other):
        if isinstance(other, Operator):
            return self.op == other.op
        return False

    @staticmethod
    def priority(op: str) -> int:
        if op == "*" or op == "+" or op == "?":
            return 3
        elif op == ".":
            return 2
        elif op == "|":
            return 1
        return 0
