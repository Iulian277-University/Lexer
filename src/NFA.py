from typing import Callable, Generic, List, Tuple, TypeVar, Dict
try:
	from AST import AST, Node
except:
	from src.AST import AST, Node
try:
	from graphviz import Digraph
except:
	print("Graphviz is not installed (NFA.py)")

"""
NFA visualization given the prenex "STAR UNION a b": https://i.imgur.com/Mju3lGb.png
"""

S = TypeVar("S")
T = TypeVar("T")

curr_state_idx = 0
visited = set()

class NFA(Generic[S]):
	def __init__(self, q0: S, qf: S, states: List[S], transitions: List[Tuple[S, str, S]], epsilonCloures: Dict = {}) -> None:
		"""
		Thompson's construction ensures that the obtained automaton has
		exactly one initial state and exactly one final state (`q0` and `qf`)
		https://en.wikipedia.org/wiki/Thompson%27s_construction#The_algorithm
		"""
		self.q0 = q0
		self.qf = qf
		self.states = states
		self.transitions = transitions
		self.epsilonClosures = epsilonCloures
		self.currentEpsilonClosure = set()


	def map(self, f: Callable[[S], T]) -> 'NFA[T]':
		""" Maps the states of type `S` of the DFA to a new type `T` """
		mappedEpsilonClosures = {}
		for state, epsCl in self.epsilonClosures.items():
			mappedEpsilonClosures[f(state)] = [f(s) for s in epsCl]
		return NFA(f(self.q0), f(self.qf), [f(s) for s in self.states],
					[(f(q0), c, f(q1)) for q0, c, q1 in self.transitions], mappedEpsilonClosures)


	def next(self, from_state: S, on_chr: str) -> 'set[S]':
		""" Returns the next states from the current state on the given character """
		return set([q1 for q0, c, q1 in self.transitions if q0 == from_state and c == on_chr])


	def getStates(self) -> 'set[S]':
		""" Returns the states of the NFA """
		return set(self.states)


	def computeEpsilonClosure(self, state: S) -> 'set[S]':
		""" Returns the epsilon closure of the given state """
		global visited
		self.currentEpsilonClosure = set()
		visited = set()

		def computeEpsilonClosureHelper(self, state: S) -> None:
			"""
			Generates the epsilon closure of the current state (using DFS traversal)
			E(q) = {state q, all states reachable by epsilon transitions from q}
			"""
			# Keep track of the visited states to avoid infinite epsilon loops
			visited.add(state)
			self.currentEpsilonClosure.add(state)

			# Get all the states that can be reached from the current state on epsilon
			next_states = self.next(state, 'eps')

			# For each of these unvisited states, get their epsilon closure and add it to the current closure
			for next_state in next_states:
				if next_state not in visited:
					computeEpsilonClosureHelper(self, next_state)

		computeEpsilonClosureHelper(self, state)
		return self.currentEpsilonClosure


	def accepts(self, str: str) -> bool:
		""" Returns true if the NFA accepts the given string, false otherwise """
		def acceptsHelper(self, expr: str, state: S) -> bool:
			"""
			Try all the possible paths from the current state to the final state
			If we reach the final state, then the NFA accepts the string
			If we don't reach the final state, then the NFA rejects the string
			"""
			# The string is consumed and the current state is a final state
			# or we can reach a final state from the current state by epsilon transitions
			if expr == '':
				return self.isFinal(state) or any(self.isFinal(state) for state in self.epsilonClosures[state])

			# The string is not consumed and compute all character transitions
			for next_state in self.next(state, expr[0]):
				if acceptsHelper(expr[1:], next_state):
					return True
			
			# The string is not consumed and compute all epsilon transitions
			for next_state in self.next(state, 'eps'):
				if acceptsHelper(expr, next_state):
					return True

			# If we couldn't find a path to a final state, then the NFA doesn't accept the string
			return False

		return acceptsHelper(self, str, self.q0)


	def isFinal(self, state: S) -> bool:
		""" Checks if the given state is a final state """
		return state == self.qf


	def atomNFA(ch: str) -> 'NFA[S]':
		""" Computes the NFA for the given atom (c, 'c', eps, void) """
		global curr_state_idx
		q0 = curr_state_idx
		qf = curr_state_idx + 1
		curr_state_idx += 2
		return NFA(q0, qf, [q0, qf], [(q0, ch, qf)])


	def concatNFA(nfa1: 'NFA[S]', nfa2: 'NFA[S]') -> 'NFA[S]':
		""" Given 2 NFAs, returns a new NFA that accepts the `concatenation` of the languages of the 2 NFAs """
		global curr_state_idx
		q0 = nfa1.q0
		qf = nfa2.qf
		return NFA(q0, qf, nfa1.states + nfa2.states,
					[(nfa1.qf, 'eps', nfa2.q0)] + nfa1.transitions + nfa2.transitions)


	def unionNFA(nfa1: 'NFA[S]', nfa2: 'NFA[S]') -> 'NFA[S]':
		""" Given 2 NFAs, returns a new NFA that accepts the `union` of the languages of the 2 NFAs """
		global curr_state_idx
		q0 = curr_state_idx
		qf = curr_state_idx + 1
		curr_state_idx += 2
		return NFA(q0, qf, [q0, qf] + nfa1.states + nfa2.states,
					[(q0, 'eps', nfa1.q0), (q0, 'eps', nfa2.q0), (nfa1.qf, 'eps', qf), (nfa2.qf, 'eps', qf)] + nfa1.transitions + nfa2.transitions)


	def starNFA(nfa: 'NFA[S]') -> 'NFA[S]':
		""" Given an NFA, returns a new NFA that accepts the `Kleene star` of the language of the given NFA """
		global curr_state_idx
		q0 = curr_state_idx
		qf = curr_state_idx + 1
		curr_state_idx += 2
		return NFA(q0, qf, [q0, qf] + nfa.states,
					[(q0, 'eps', nfa.q0), (nfa.qf, 'eps', qf), (q0, 'eps', qf), (nfa.qf, 'eps', nfa.q0)] + nfa.transitions)


	def plusNFA(nfa: 'NFA[S]') -> 'NFA[S]':
		""" Given an NFA, returns a new NFA that accepts the `plus` of the language of the given NFA """
		global curr_state_idx
		q0 = curr_state_idx
		qf = curr_state_idx + 1
		curr_state_idx += 2
		return NFA(q0, qf, [q0, qf] + nfa.states,
					[(q0, 'eps', nfa.q0), (nfa.qf, 'eps', qf), (nfa.qf, 'eps', nfa.q0)] + nfa.transitions)


	def maybeNFA(nfa: 'NFA[S]') -> 'NFA[S]':
		""" Given an NFA, returns a new NFA that accepts the `maybe` of the language of the given NFA """
		return NFA(nfa.q0, nfa.qf, nfa.states, [(nfa.q0, 'eps', nfa.qf)] + nfa.transitions)


	@staticmethod
	def isAtom(token: str) -> bool:
		""" Checks if the given character is an atom (c, 'c', eps, void) """
		# Empty token
		if len(token) == 0:
			return False

		# Character
		if len(token) == 1:
			return True 
		
		# Chracter surrounded by single quotes
		if token[0] == "'" and token[-1] == "'" and len(token) == 3:
			return True
		
		# `eps` or `void`
		return token in ['eps', 'void']


	@staticmethod
	def fromAST(root: Node) -> 'NFA[int]':
		"""  Recursively builds an NFA from the given regular expression (in prenex form) """
		if NFA.isAtom(root.token):
			return NFA.atomNFA(root.token)
		if root.token == 'STAR':
			return NFA.starNFA(NFA.fromAST(root.children[0]))
		if root.token == 'PLUS':
			return NFA.plusNFA(NFA.fromAST(root.children[0]))
		if root.token == 'MAYBE':
			return NFA.maybeNFA(NFA.fromAST(root.children[0]))
		if root.token == 'CONCAT':
			return NFA.concatNFA(NFA.fromAST(root.children[0]), NFA.fromAST(root.children[1]))
		if root.token == 'UNION':
			return NFA.unionNFA(NFA.fromAST(root.children[0]), NFA.fromAST(root.children[1]))


	@staticmethod
	def fromPrenex(prenex: str) -> 'NFA[int]':
		""" Computes the AST from the given regular expression and then builds an NFA from it """
		global curr_state_idx, visited
		curr_state_idx = 0
		ast = AST(prenex)
		ast.fromPrenex()
		nfa = NFA.fromAST(ast.getRoot())
		# Compute the epsilon closure of each state and reset some global vars
		for state in nfa.states:
			nfa.epsilonClosures[state] = nfa.computeEpsilonClosure(state)
		visited = set()
		return nfa


	def visualize(self, filename: str) -> None:
		""" Dumps the NFA to a dot file using Graphviz """
		dot = Digraph(comment='NFA')
		dot.attr(rankdir='LR', size='10')
		for state in self.states:
			if self.isFinal(state):
				dot.node(str(state), str(state), shape='doublecircle')
			else:
				dot.node(str(state), str(state))
		for transition in self.transitions:
			dot.edge(str(transition[0]), str(transition[2]), label=transition[1])
		try:
			dot.render(filename)
		except:
			print(f"Couldn't render the NFA `{filename}`, but saved it to a dot file.")
