import re
import sys
import pycosat

_read_error_msg = 'Impossible de lire le fichier'
_usage_msg = 'Usage : {} <{}> <{}>'
_wcnf_file_msg = 'fichier.wcnf'
_dnf_msg = 'Clause FND'
_sigma_msg = 'Sigma ='
_phi_msg = 'Phi ='
_val_msg = 'Val(Phi, Sigma) ='


def load_weighted_knowledge_base(file_path):
    """
    Return the content of a WCNF file.
    :param file_path: The path of the WCNF file.
    :return: A list of lists where each inner list contains the weight and the variables of a DNF clause.
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
                line_variables[0] = float(line_variables[0])
                line_variables[1:] = [int(x) for x in line_variables[1:-1]]
                weighted_clauses.append(line_variables)  # All variables except the 0
    return weighted_clauses


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
    :param knowledge_base_wc: A list of lists where each list contains the weight and the variables (Sigma).
    :param clause: A list containing variables (Phi).
    :return: The value of inconsistency Val(Sigma U neg(Phi)).
    """
    r = 0  # Just an initialisation
    l = 0
    u = len(knowledge_base_wc)
    knowledge_base_c = [x[1:] for x in knowledge_base_wc]  # Remove the weights
    while l < u:
        r = (l + u) // 2  # Integer division
        if isinstance(pycosat.solve(knowledge_base_c[l:u] + negation(clause)), list):  # Picosat found a solution
            u = r - 1
        else:
            l = r
    return knowledge_base_wc[r][0]  # Weight of the clause

if __name__ == '__main__':
    if len(sys.argv) == 3:
        try:
            Sigma = load_weighted_knowledge_base(sys.argv[1])  # WCNF file
            print(_sigma_msg, end=' ')
            if len(Sigma) > 10:
                print('[', str(Sigma[:3])[1:-1], '...', str(Sigma[-3:])[1:-1], ']')
            else:
                print(Sigma)
            Phi = [int(x) for x in re.split('\s+', sys.argv[2])]  # DNF clause
            print(_phi_msg, Phi)
            val = inconsistency_degree(Sigma, Phi)
            print(_val_msg, val)
        except FileNotFoundError as e:
            print(_read_error_msg, e.filename, file=sys.stderr)
    else:
        print(_usage_msg.format(sys.argv[0], _wcnf_file_msg, _dnf_msg), file=sys.stderr)
