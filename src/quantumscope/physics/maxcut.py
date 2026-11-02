"""MaxCut on small graphs, for QAOA (Qt-free).

A cut colours each node 0 or 1; its value is the number of edges joining different colours.
QAOA minimises H = Σ_edges ½(Z_i Z_j − 1) = −(number of cut edges), whose minimum is
−(maximum cut). Bit k of a measured bitstring is node k's colour.
"""
import itertools

# name -> (label, nodes, edges, node positions on a unit square for drawing)
GRAPHS = {
    'ring4': ('Square (4 nodes)', 4, ((0, 1), (1, 2), (2, 3), (3, 0)),
              ((0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8))),
    'diamond': ('Square with a diagonal (4 nodes)', 4, ((0, 1), (1, 2), (2, 3), (3, 0), (0, 2)),
                ((0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8))),
    'ring5': ('Pentagon (5 nodes, odd)', 5, ((0, 1), (1, 2), (2, 3), (3, 4), (4, 0)),
              ((0.5, 0.1), (0.88, 0.38), (0.74, 0.85), (0.26, 0.85), (0.12, 0.38))),
    'ring6': ('Hexagon (6 nodes)', 6, ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)),
              ((0.3, 0.1), (0.7, 0.1), (0.9, 0.5), (0.7, 0.9), (0.3, 0.9), (0.1, 0.5))),
    'prism': ('Triangular prism (6 nodes, 3 edges each)', 6,
              ((0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (0, 3), (1, 4), (2, 5)),
              ((0.5, 0.08), (0.12, 0.8), (0.88, 0.8), (0.5, 0.36), (0.32, 0.66), (0.68, 0.66))),
}


def cut_value(bits, edges):
    """Number of edges whose ends differ; bits is a string like '0101' (node k = bits[k])."""
    return sum(bits[i] != bits[j] for i, j in edges)


def best_cuts(n, edges):
    """(maximum cut value, all bitstrings achieving it) by brute force."""
    values = {''.join(b): cut_value(''.join(b), edges) for b in itertools.product('01', repeat=n)}
    best = max(values.values())
    return best, sorted(b for b, v in values.items() if v == best)


def hamiltonian(edges):
    """H = Σ ½ Z_i Z_j − ½|E|: its expectation is minus the expected number of cut edges."""
    return ' + '.join(f'0.5 Z{i} Z{j}' for i, j in edges) + f' - {0.5 * len(edges):g}'


def expected_cut(probabilities, edges):
    """Average cut value over a {bitstring: probability} distribution."""
    return sum(p * cut_value(b, edges) for b, p in probabilities.items())
