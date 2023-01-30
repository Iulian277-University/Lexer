from typing import Callable, Generic, List, Tuple, TypeVar
try:
	from NFA import NFA
except:
	from src.NFA import NFA
try:
	from graphviz import Digraph
except:
	print("Graphviz is not installed (DFA.py)")

"""
DFA visualization given the prenex "STAR UNION a b": https://i.imgur.com/V1RRC6f.png
"""

S = TypeVar("S")
T = TypeVar("T")

class DFA(Generic[S]):
	def __init__(self, q0: S, qfs: List[S], states: List[S], transitions: List[Tuple[S, str, S]], sink: S = None):
		"""
		The DFA is represented as a tuple of the form (Q, Σ, δ, q0, F)
		where Q is the set of states, Σ is the alphabet, δ is the transition function,
		q0 is the initial state and F is the set of final states
		https://en.wikipedia.org/wiki/Deterministic_finite_automaton#Definition
		"""
		self.q0  = q0
		self.qfs = qfs
		self.states = states
		self.transitions = transitions
		self.sink = sink


	def map(self, f: Callable[[S], T]) -> 'DFA[T]':
		""" Maps the states of type `S` of the DFA to a new type `T` """
		return DFA(f(self.q0), [f(s) for s in self.qfs], [f(s) for s in self.states], 
					[(f(q0), c, f(q1)) for q0, c, q1 in self.transitions], f(self.sink))


	def next(self, from_state: S, on_chr: str) -> S:
		"""
		Returns the next state given the current state and a character
		or None if the transition is undefined
		"""
		for state, c, next_state in self.transitions:
			if state == from_state and c == on_chr:
				return next_state
		return None


	def getStates(self) -> 'set[S]':
		""" Returns the set of states reachable from the given state """
		return set(self.states)


	def accepts(self, str: str) -> bool:
		""" Checks if the given string is accepted by the DFA """
		state = self.q0
		for c in str:
			state = self.next(state, c)
			# Check if the transition is undefined -> sink state
			if state is None:
				return False
		return self.isFinal(state)


	def isFinal(self, state: S) -> bool:
		""" Returns true if the given state is a final state """
		return state in self.qfs
	

	@staticmethod
	def setToStr(states: 'set[S]') -> str:
		"""
		Converts a set of states of type `S` to a group of states of type `str`
		with the following form: "q0_q1_q2_..._qn"
		"""
		return '_'.join([str(state) for state in sorted(states)])
		

	@staticmethod
	def strToSet(str: str) -> 'set[S]':
		""" Converts a group of state of the form "q0_q1_q2_..._qn" to a set of states of type `S` """
		return set([int(state) for state in str.split('_') if len(state) > 0])


	@staticmethod
	def getAlphabet(nfa: 'NFA[S]') -> 'set[str]':
		""" Returns the alphabet known by the DFA """
		alphabet = set()
		for _, c, _ in nfa.transitions:
			if c != 'eps':
				alphabet.add(c)
		return sorted(alphabet)


	@staticmethod
	def fromNFA(nfa: NFA[S]) -> 'DFA[S]':
		"""
		Performs the subset construction algorithm to convert an NFA to a DFA
		https://en.wikipedia.org/wiki/Powerset_construction
		"""
		# The first group is the epsilon closure of the initial state
		alphabet = DFA.getAlphabet(nfa)
		q0_group = DFA.setToStr(nfa.epsilonClosures[nfa.q0])
		dfa = DFA(q0_group, [], [q0_group], [])

		# `last_groups` works like a queue, because we take the first group at each iteration
		# (using the `for loop`) and add the new groups of state to the end of the list (using `append`)		
		last_groups = [q0_group]
		for last_group in last_groups:
			for ch in alphabet:
				next_state_group = set()
				for state in DFA.strToSet(last_group):
					next_states = nfa.next(state, ch)
					for next_state in next_states:
						next_state_group = next_state_group.union(nfa.epsilonClosures[next_state])

				# Update the DFA
				if DFA.setToStr(next_state_group) not in dfa.states:
					dfa.states.append(DFA.setToStr(next_state_group))
					last_groups.append(DFA.setToStr(next_state_group))
				
				# Add the transition
				dfa.transitions.append((last_group, ch, DFA.setToStr(next_state_group)))
		
		# If the group contains the final state of the NFA, then the group is a final state of the DFA
		dfa.qfs = [state for state in dfa.states if str(nfa.qf) in state]

		# Map the DFA states to integers, starting from index `counter`
		class DFAMapper():
			def __init__(self, counter=0) -> None:
				self.counter = counter
				self.mapping = {}

			def get_mapping(self, x):
				if x not in self.mapping:
					self.mapping[x] = self.counter
					self.counter += 1

				return self.mapping[x]

		dfa = dfa.map(DFAMapper().get_mapping)

		# Set sink state
		for state in dfa.states:
			if all([dfa.next(state, ch) is state for ch in alphabet]) and not dfa.isFinal(state):
				dfa.sink = state
				break

		# If there is no sink state, create one and add the undefined transitions to it
		if dfa.sink is None:
			dfa.sink = len(dfa.states) + 1
			dfa.states.append(dfa.sink)
			# Append transitions to the sink state
			for state in dfa.states:
				for ch in alphabet:
					if dfa.next(state, ch) is None:
						dfa.transitions.append((state, ch, dfa.sink))

		return dfa


	@staticmethod
	def fromPrenex(prenex: str) -> 'DFA[int]':
		""" Computes the NFA from the given prenex and then converts it to a DFA """
		nfa = NFA.fromPrenex(prenex)
		return DFA.fromNFA(nfa)


	def visualize(self, filename: str) -> None:
		""" Dumps the DFA to a dot file using Graphviz """
		dot = Digraph(comment='DFA')
		dot.attr(rankdir='LR', size='10')
		dfa = self.map(str)
		for state in dfa.states:
			if dfa.isFinal(state):
				dot.node(state, state, shape='doublecircle')
			else:
				dot.node(state, state)
		for state, c, next_state in dfa.transitions:
			dot.edge(state, next_state, label=c)
		try:
			dot.render(filename)
		except:
			print(f"Couldn't render the DFA `{filename}`, but saved it to a dot file.")
