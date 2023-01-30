from __future__ import annotations
from typing import Tuple, List, Dict
from collections import defaultdict
try:
	from NFA import NFA
except:
	from src.NFA import NFA
try:
    from DFA import DFA
except:
    from src.DFA import DFA
try:
    from Parser import Parser
except:
    from src.Parser import Parser

class Lexer:
    def __init__(self, configurations: Dict[str, str]) -> None:
        """
        This constructor initializes the lexer with a configuration
        The configuration is passed as a dictionary TOKEN -> REGEX
        """
        self.configurations = configurations
        # Replace \( with \'(\' and \) with \')\' and so on for each token in the configuration
        # This is allows us to use control characters (e.g.: +, *) as being normal characters, not operators
        for token, regex in self.configurations.items():
            configurations[token] = regex \
                .replace("\\(", "\'(\'") \
                .replace("\\)", "\')\'") \
                .replace("\\*", "\'*\'") \
                .replace("\\+", "\'+\'")

        # For every configuration, create a DFA and store it in a dictionary
        # The key is the token and the value is the DFA
        self.dfas = {}
        counter = 0
        for token, regex in self.configurations.items():
            prenex = Parser.toPrenex(regex)
            nfa = NFA.fromPrenex(prenex)
            dfa = DFA.fromNFA(nfa)
            dfa = dfa.map(lambda x: x + counter)
            counter += len(nfa.states)
            self.dfas[token] = dfa


    def getLongestMatch(self, matchesDict) -> Tuple[str, int] | None:
        """
        Given a list of matches, returns the longest match
        If there are multiple longest matches, returns the one with the highest priority
        If the list is empty, returns None
        """
        # If there are no matches, return None
        if len(matchesDict) == 0:
            return None

        # Get the longest match and traverse the list backwards
        # in order to get the longest match with the highest priority
        longestMatchIdx   = 0
        longestMatchToken = None
        for token, matches in reversed(matchesDict.items()):
            for match in matches:
                if match >= longestMatchIdx:
                    longestMatchIdx = match
                    longestMatchToken = token
        
        return (longestMatchToken, longestMatchIdx)


    def lex(self, word: str) -> List[Tuple[str, str]] | str:
        """
        The main functionality of the lexer, receives a word and lexes it
        according to the provided configuration.
        The return value is either a List of tuples (TOKEN, LEXEM) if the lexer succedes
        or a string message if the lexer fails
        """
        output = []
        start_idx = 0
        # While there are still characters to lex
        while start_idx < len(word):
            matches = defaultdict(list[tuple[int, int]])
            num_sinks = 0
            failed_curr_idx = 0
            
            # For every DFA, try to match the longest possible string
            for token, dfa in self.dfas.items():
                curr_idx = start_idx
                curr_state = dfa.q0
                # While there are still characters to lex and the current state is not a sink
                while curr_idx < len(word):
                    # Get the next state based on the current state and the current character
                    curr_char  = word[curr_idx]
                    curr_state = dfa.next(curr_state, curr_char)
                    # If the current state is a final state, save the index and the state
                    if curr_state in dfa.qfs:
                        matches[token].append(curr_idx)
                    # If the current state is a sink, count the number of sinks and break
                    if curr_state == None or curr_state == dfa.sink:
                        num_sinks += 1
                        break
                    curr_idx += 1
                # Failed index is the highest index that failed to lex
                failed_curr_idx = max(failed_curr_idx, curr_idx)
                # Stop the loop if all the DFAs are in a sink state (don't waste time by looping in the sink)
                if num_sinks == len(self.dfas):
                    break

            # Try to get the longest match, but if there are no matches, return an error message
            try:
                longestToken, longestIdx = self.getLongestMatch(matches)
                output.append((longestToken, word[start_idx : longestIdx + 1]))
                start_idx = longestIdx + 1
            except:
                # Single line input
                if word.count('\n') == 0:
                    if failed_curr_idx == len(word):
                        return f'No viable alternative at character EOF, line 0'
                    else:
                        return f'No viable alternative at character {failed_curr_idx}, line 0'
                # Multiple lines input - compute the line number and the character index in that specific line
                else:
                    line = 0
                    for i, char in enumerate(word):
                        if char == '\n':
                            line += 1
                        if i == failed_curr_idx:
                            break
                    if failed_curr_idx == len(word):
                        return f'No viable alternative at character EOF, line {line}'
                    # Compute `failed_curr_idx` in the current line
                    failed_curr_idx = failed_curr_idx - word[:failed_curr_idx].rfind('\n')
                    return f'No viable alternative at character {failed_curr_idx}, line {line}'

        return output
