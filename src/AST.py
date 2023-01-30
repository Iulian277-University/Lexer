from typing import List
try:
	from graphviz import Digraph
except:
	print("Graphviz is not installed (AST.py)")

"""
AST visualization given the prenex "STAR UNION a b": https://i.imgur.com/ICNRw66.png
"""

graphviz_idx = 0
class Node:
    def __init__(self, token: str, num_children: int, children: List['Node']) -> None:
        """ The node contains a token, a graphviz label, the number of children, and a list of children """
        global graphviz_idx
        self.token = token
        self.graphviz_token = token + '_' + str(graphviz_idx)
        graphviz_idx += 1
        self.num_children = num_children
        self.children = children

    def __str__(self):
        return self.token

class AST:
    @staticmethod
    def customSplit(prenex: str) -> List[str]:
        """
        Splits the given prenex expression into a list of tokens and then converts
        the tokens of the form "'c'" into "c" (this allows us to use <space> as a token)
        """
        # Split the prenex into tokens
        tokens = []
        token = ""
        in_quotes = False
        for char in prenex:
            if char == "'":
                in_quotes = not in_quotes
            if char == " " and not in_quotes:
                tokens.append(token)
                token = ""
            else:
                token += char
        tokens.append(token)
        
        # Convert "'c'" to "c"
        for token in tokens:
            if len(token) == 3 and token[0] == "'" and token[2] == "'":
                tokens[tokens.index(token)] = token[1]

        return tokens


    def __init__(self, prenex: str) -> None:
        """
        The AST is represented as a list of nodes (with the form specified above),
        a list of tokens, and an iterator over the tokens
        """
        self.nodes = []
        self.tokens_list = AST.customSplit(prenex)
        self.tokens_list_iter = iter(self.tokens_list)


    def getRoot(self) -> Node:
        """ Returns the root of the AST or None if the AST is empty  """
        if len(self.nodes) == 0:
            return None
        return self.nodes[0]


    def visualize(self, filename: str) -> None:
        """ Dump the AST to a dot file using Graphviz """
        def visualizeHelper(node, graph, parent_node=None):
            if node == None:
                return
            graph.node(node.graphviz_token)
            if parent_node != None:
                graph.edge(parent_node.graphviz_token, node.graphviz_token)
            for child in node.children:
                visualizeHelper(child, graph, node)

        graph = Digraph()
        graph.attr(rankdir='UD', size='10', shape='circle')
        visualizeHelper(self.getRoot(), graph)
        graph.save(filename)


    def display(self, node, level=0) -> None:
        """ Print the AST in a tree-like format """
        if node == None:
            return
        print("  " * level, node)
        for child in node.children:
            self.display(child, level + 1)


    def createNode(self, token: str) -> Node:
        """ Creates a node with the given token, setting the expected number of children """
        if token in ["STAR", "PLUS", "MAYBE"]:
            num_children = 1
        elif token in ["UNION", "CONCAT"]:
            num_children = 2
        else: # atom (c, 'c', eps, void)
            num_children = 0

        return Node(token, num_children, [])


    def fromPrenex(self) -> Node:
        """ Parse the prenex expression and sets the AST's nodes """
        token = next(self.tokens_list_iter)
        node  = self.createNode(token)
        self.nodes.append(node)
        for _ in range(node.num_children):
            node.children.append(self.fromPrenex())
        return node
