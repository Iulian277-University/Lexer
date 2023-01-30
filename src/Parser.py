from __future__ import annotations
try:
    from src.Regex import Character, Operator
except:
    from Regex import Character, Operator

STAR    = Operator("*")
PLUS    = Operator("+")
MAYBE   = Operator("?")
UNION   = Operator("|")
CONCAT  = Operator(".")
L_BRACK = Operator("(")
R_BRACK = Operator(")")

class Parser:
    @staticmethod
    def addConcatOp(rlist: list[Character | Operator]) -> list[Character | Operator]:
        """
        Adds concatenation operator between items in the list in the following cases:
        - ab
        - a(
        - )a
        - )(
        - *a, +a, ?a
        - *(, +(, ?(
        """
        # If the list has only one item, it is not needed to add concatenation
        if len(rlist) == 1:
            return rlist

        out = []
        i = 0
        for i in range(len(rlist) - 1):
            if isinstance(rlist[i], Character) and isinstance(rlist[i + 1], Character): # ab
                out.append(rlist[i])
                out.append(CONCAT)
            elif isinstance(rlist[i], Character) and rlist[i + 1] == L_BRACK: # a(
                out.append(rlist[i])
                out.append(CONCAT)
            elif rlist[i] == R_BRACK and isinstance(rlist[i + 1], Character): # )a
                out.append(rlist[i])
                out.append(CONCAT)

            elif rlist[i] == R_BRACK and rlist[i + 1] == L_BRACK: # )(
                out.append(rlist[i])
                out.append(CONCAT)

            elif rlist[i] == STAR and isinstance(rlist[i + 1], Character): # *a
                out.append(rlist[i])
                out.append(CONCAT)
            elif rlist[i] == PLUS and isinstance(rlist[i + 1], Character): # +a
                out.append(rlist[i])
                out.append(CONCAT)
            elif rlist[i] == MAYBE and isinstance(rlist[i + 1], Character): # ?a
                out.append(rlist[i])
                out.append(CONCAT)

            elif rlist[i] == STAR and rlist[i + 1] == L_BRACK: # *(
                out.append(rlist[i])
                out.append(CONCAT)
            elif rlist[i] == PLUS and rlist[i + 1] == L_BRACK: # +(
                out.append(rlist[i])
                out.append(CONCAT)
            elif rlist[i] == MAYBE and rlist[i + 1] == L_BRACK: # ?(
                out.append(rlist[i])
                out.append(CONCAT)
            else:
                out.append(rlist[i])
                
        out.append(rlist[i + 1])
        return out


    @staticmethod
    def preprocess(regex: str) -> list[Character | Operator]:
        """
        Preprocess the regex string and returns a list of characters and operators
        -> Classify input as either character(or string) or operator
        -> Convert special inputs like [0-9], [a-z] and [A-Z] to their correct form
        -> Convert escaped characters
        """
        # Replace "eps" with "ε"
        regex = regex.replace("eps", "ε")

        # Classify input as either character(or string) or operator
        rlist = []
        i = 0
        while i < len(regex):
            # Escaped characters
            if regex[i] == "\'":
                i += 1 # Skip the first \' character
                if regex[i] == "\n":
                    rlist.append(Character("'\n'"))
                elif regex[i] == "\t":
                    rlist.append(Character("'\t'"))
                elif regex[i] == "\r":
                    rlist.append(Character("'\r'"))
                elif regex[i] == " ":
                    rlist.append(Character("' '"))
                else:
                    rlist.append(Character(regex[i]))
                i += 1 # Skip the last \' character
            # Operators
            elif regex[i] == '(':
                rlist.append(L_BRACK)
            elif regex[i] == ')':
                rlist.append(R_BRACK)
            elif regex[i] == '*':
                rlist.append(STAR)
            elif regex[i] == '+':
                rlist.append(PLUS)
            elif regex[i] == '?':
                rlist.append(MAYBE)
            elif regex[i] == '|':
                rlist.append(UNION)
            elif regex[i] == '.':
                rlist.append(CONCAT)
            # Special inputs like [0-9], [a-z] and [A-Z]
            elif regex[i] == '[':
                # [0-9] -> (0|1|2|3|4|5|6|7|8|9)
                first = regex[i + 1]
                last  = regex[i + 3]
                rlist.append(L_BRACK)
                for j in range(ord(first), ord(last)):
                    rlist.append(Character(chr(j)))
                    rlist.append(UNION)
                rlist.append(Character(last))
                rlist.append(R_BRACK)
                i += 4 # Skip the last ] character
            else:
                rlist.append(Character(regex[i]))
            i += 1

        # Add concatenation operator
        # print(rlist)
        rlist = Parser.addConcatOp(rlist)
        # print(rlist)
        return rlist


    @staticmethod
    def toPrenexHelper(regex: list[Character | Operator]) -> str:
        """
        Given a list of Character and Operator instances, convert it to prenex form
        For this, use a stack to keep track of the operators

        Based on the current item, perform the following operations:
            - If the current item is an `character`, add it to the output
            - If the item is a `left bracket`, push it to the stack
            - If the item is a `right bracket`, pop all the operators from the stack and add them to the output
            until find a left bracket. Then pop the left bracket from the stack
            - If the item is an `operator`, pop all the operators with higher (or equal for STAR operator) precedence
            from the stack and add them to the output. Then push the current operator to the stack

        Clear the stack and add all the items to the output
        At the end, reverse the output and convert from regex symbols to prenex symbols
        Clear some extra spaces and replace back the `ε` symbol with `eps`
        """
        out = []
        stack = []
        for i in range(len(regex)):
            if isinstance(regex[i], Character):
                out.append(regex[i])
            elif isinstance(regex[i], Operator):
                if regex[i] == L_BRACK:
                    stack.append(regex[i])
                elif regex[i] == R_BRACK:
                    while stack[-1] != L_BRACK:
                        out.append(stack.pop())
                    stack.pop()
                else:
                    if regex[i] == STAR:
                        while regex[i].priority <= stack[-1].priority: 
                            out.append(stack.pop())
                    else:
                        while regex[i].priority < stack[-1].priority: 
                            out.append(stack.pop())
                    stack.append(regex[i])

        # Add remaining elements to output
        while len(stack) > 0:
            out += stack.pop()

        # Convert from regex symbols to prenex symbols (traverse the list `out` in reverse order)
        prefix = ""
        for i in range(len(out) - 1, -1, -1):
            if isinstance(out[i], Operator):
                if out[i].op == '.':
                    prefix += "CONCAT "
                elif out[i].op == '|':
                    prefix += "UNION "
                elif out[i].op == '*':
                    prefix += "STAR "
                elif out[i].op == '+':
                    prefix += "PLUS "
                elif out[i].op == '?':
                    prefix += "MAYBE "
            else:
                prefix += out[i].chr + " "
            
        # Remove the extra spaces before and after \n, \r and \t
        prefix = prefix.replace(" \n ", "\n")
        prefix = prefix.replace(" \r ", "\r")
        prefix = prefix.replace(" \t ", "\t")

        # Replace "ε" with "eps"
        prefix_rev = prefix[:-1].replace("ε", "eps")
        return prefix_rev


    @staticmethod
    def toPrenex(regex: str) -> str:
        """
        This function constructs a prenex expression out of a normal one
        It uses an algorithm for converting infix to prefix regex (prenex)
        -> Preprocess the regex string into a list of characters and operators
        -> Reverse the list
        -> Swap '(' with ')' and vice versa
        -> Add the entire regex between '(' and ')'
        -> Call `toPrenexHelper()` to convert the list to a prenex expression
        """
        rlist = Parser.preprocess(regex)
        rlist = reversed(rlist)
        infix_list = []
        for x in rlist:
            if x == L_BRACK:
                infix_list.append(R_BRACK)
            elif x == R_BRACK:
                infix_list.append(L_BRACK)
            else:
                infix_list.append(x)

        infix_list = [L_BRACK] + infix_list + [R_BRACK]
        prenex = Parser.toPrenexHelper(infix_list)
        return prenex
