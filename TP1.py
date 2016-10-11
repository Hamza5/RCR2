import re
import sys
import pycosat
from numbers import Real, Integral

_read_error_msg = 'Impossible de lire le fichier'
_usage_msg = 'Usage : {} <{}> <{}>'
_wcnf_file_msg = 'fichier.wcnf'
_dnf_msg = 'Clause FND'
_sigma_msg = 'Sigma ='
_phi_msg = 'Phi ='
_val_msg = 'Val(Phi, Sigma) ='
_interest_msg = 'Variable ='


def load_weighted_knowledge_base(file_path):
    """
    Return the content of a WCNF file.
    :param file_path: The path of the WCNF file.
    :return: A WeightedKnowledgeBase.
    """
    with open(file_path) as kb_file:
        line_regexp = re.compile('\d+(?:\.\d+)?\s+(?:(-?\d+)\s+)+0')
        separator_regexp = re.compile('\s+')
        weighted_clauses = []
        for line in kb_file:
            line = line.strip()
            if not line or line.startswith('c') or re.match('p\s+wcnf\s+(\d+)\s+(\d+)', line, re.IGNORECASE):
                continue  # Skip empty lines, comments and header
            elif re.match(line_regexp, line):
                line_variables = re.split(separator_regexp, line)
                weighted_clauses.append([float(line_variables[0])] + [int(x) for x in line_variables[1:-1]])
    return WeightedKnowledgeBase(weighted_clauses)


def negation(dnf_clause):
    """
    Return the negation of a DNF clause.
    :param dnf_clause: A list containing the variables of the clause in DNF format.
    :return: A list of lists where each one contains single variable negated.
    """
    return [[-x] for x in dnf_clause]


def inconsistency_degree(knowledge_base_wc, clause):
    """
    Return the inconsistency degree of knowledge_base_wc union the negation of clause using the refutation.
    :param knowledge_base_wc: A WeightedKnowledgeBase (Sigma).
    :param clause: A list containing variables (Phi).
    :return: The value of inconsistency Val(Sigma U neg(Phi)).
    """
    assert isinstance(knowledge_base_wc, WeightedKnowledgeBase)
    r = 0  # Just an initialisation
    l = 0
    u = len(knowledge_base_wc)
    while l < u:
        r = (l + u) // 2  # Integer division
        if isinstance(pycosat.solve([list(x) for x in knowledge_base_wc[r:u]] + negation(clause)), list):
            # Picosat found a solution
            u = r - 1
        else:
            l = r
    return knowledge_base_wc.weights[r]  # Weight of the clause


class WeightedClause:
    """
    Represent a DNF clause with an associated weight.

    Inspired from an idea by Abdelkarim (Walid) Boumehdi :)
    """

    def __init__(self, weight, dnf_clause):
        assert isinstance(weight, Real)
        self.weight = weight
        assert isinstance(dnf_clause, list) and all([isinstance(x, Integral) for x in dnf_clause])
        self.clause = dnf_clause

    def __eq__(self, other):
        assert isinstance(other, WeightedClause)
        return self.weight == other.weight

    def __lt__(self, other):
        assert isinstance(other, WeightedClause)
        return self.weight < other.weight

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getitem__(self, item):
        return self.clause[item]

    def __len__(self):
        return len(self.clause)

    def __str__(self):
        return '(' + str(self.clause) + ', ' + str(self.weight) + ')'

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        return iter(self.clause)


class WeightedKnowledgeBase:
    """
    Represent a CNF base of weighted DNF clauses.
    """

    def __init__(self, kb_wc=list()):
        assert isinstance(kb_wc, list) and all([isinstance(x, list) for x in kb_wc])
        self.clauses = {}
        for x in kb_wc:
            weighted_clause = WeightedClause(x[0], x[1:])
            self.add_clause(weighted_clause)
        self.weights = [w for w in sorted(self.clauses.keys())]

    def add_clause(self, w_clause):
        assert isinstance(w_clause, WeightedClause)
        if w_clause.weight not in self.clauses:
            self.clauses[w_clause.weight] = [w_clause]
        else:
            self.clauses[w_clause.weight].append(w_clause)

    def __len__(self):
        return len(self.weights)

    def __getitem__(self, item):
        if isinstance(item, slice):
            items = []
            for i in range(item.start, item.stop):
                items += self.clauses[self.weights[i]]
            return [list(x) for x in items]
        else:
            return [list(x) for x in self.clauses[self.weights[item]]]


if __name__ == '__main__':
    if len(sys.argv) == 3:
        try:
            Sigma = load_weighted_knowledge_base(sys.argv[1])  # WCNF file
            Phi = [int(x) for x in re.split('\s+', sys.argv[2])]  # DNF clause
            print(_phi_msg, Phi)
            val = inconsistency_degree(Sigma, Phi)
            print(_val_msg, val)
            print(_interest_msg, Sigma.clauses[val])
        except FileNotFoundError as e:
            print(_read_error_msg, e.filename, file=sys.stderr)
    else:
        print(_usage_msg.format(sys.argv[0], _wcnf_file_msg, _dnf_msg), file=sys.stderr)
