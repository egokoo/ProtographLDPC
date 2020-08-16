from libs.Identity import Identity
from libs.RegularLDPC import RegularLDPC

from libs.TannerGraph import *

'''
- A class for the handling of ProtogrpahLDPC matrices in Tanner Graph form

The tanner graph is stored as a dictionary, row indices (check nodes) are mapped to lists of column indices (variable
nodes) to indicate bipartite connections

args: input to enable construction. input follows the following construction pattern: args[0] = Protograph object
containing the Protograph to be lifted. args[1] depicts the factor by which to lift the given protograph.

The construction argument indicates the algorithm to be employed in the construction of protograph submatrices. These
submatrices are defined by the following scope: (rows: r => r + f, columns: c => c + f) for all (r, c) where r % f == 0
and c % f == 0. f is the supplied protograph lift factor.

The implemented constructions work as follows:

construction = permutation
This submatrix is a result of the sum of n (non-overlapping) permutation matrices of width f, where n is
defined by the position at row = r / f, column = c / f on the supplied protograph.

construction = regular
This submatrix is a regular LDPC matrix graph whose row and column weightage is defined by the protograph's value
at row = r / f, column = c / f.

construction = quasi-cyclic
Given a list of n randomly chosen indices, where n is defined by the value of the protogrpah at (r, c) and n is
bounded by the width of the submatrix, this list represents the entries for the first row of the code. For every
subsequent row in the submatrix, that row is defined by the circular right shift of the previous row.

construction = permuted-quasi-cyclic
Similar to quasi-cyclic but the rows and columns of the submatrix are permuted.
'''

class ProtographLDPC(TannerGraph):

    # parameters:
    #   protograph to be lifted
    #   lift factor
    #   construction method
    # return:
    #   a fully lifted Protograph LDPC code
    def __init__(self, protograph, factor, construction):
        TannerGraph.__init__(self, [protograph, factor], construction=construction)

        self.construction = construction
        self.protograph = protograph
        self.factor = factor

        self.maximum_allowable_protograph_node = self.factor

        self.width = self.protograph.width * self.factor
        self.height = self.protograph.height * self.factor

        self.tanner_graph = ProtographLDPC.expanded_protograph(self.protograph, self.factor, self.construction)

    '''
    This method provides a means by which a given protograph can be lifted by a given factor. This method cannot identify
    if a supplied permutation set does not fit the provided lift factor, so if unsure, do not supply this method with a
    permutation set. The option to provide your own set is for the purposes of not creating redundant objects.
    '''
    # parameters:
    #   protograph: Protograph, the protograph code which must be lifted
    #   factor: the factor by which to lift the protograph
    # return:
    #   ProtographLDPC, fully expanded
    @staticmethod
    def expanded_protograph(protograph, factor, construction):

        expanded = TannerGraph(None)
        for i in range(protograph.height * factor):
            expanded.addRow()

        for r in range(0, len(expanded), factor):
            for c in range(0, protograph.width * factor, factor):

                if protograph.get(r / factor, c / factor) > factor:
                    raise RuntimeError("Invalid protograph value for given lift factor")


                elif protograph.get(r / factor, c / factor) == 0:
                    continue

                else:

                    expanded.insert(ProtographLDPC.submatrix(
                        submatrix_construction=construction,
                        factor=factor,
                        num_ones_per_row=protograph.get(r / factor, c / factor)
                    ), [r, c])

        return expanded.tanner_graph

    # parameters:
    #   num_ones_per_row: the number of ones per column/row. This is bounded by the lifting factor of the protograph
    #   as all submatrices are of dimension width = factor, height = factor.
    #   factor: the lifting factor by which the associated protograph is to be lifted by
    #   submatrix_construction: the algorithm through which the submatrix is constructed
    # returns:
    #   submatrix: TannerGraph, graph to be inserted into the eventual code
    @staticmethod
    def submatrix(submatrix_construction="regular", factor=None, num_ones_per_row=None):

        if submatrix_construction == "permutation":
            # start with a random permutation
            start = Identity(random.sample(range(factor),factor))

            if num_ones_per_row == 1:
                return start # we are done

            for i in range(num_ones_per_row - 1):
                # in this case we need to add in more permutations,
                # but we need to make sure they are non-overlapping
                while True:
                    trial_permutation = Identity(random.sample(range(factor),factor))
                    if not start.overlaps(trial_permutation):
                        start = start.absorb_nonoverlapping(trial_permutation,[0, 0])
                        break
            return start

        elif submatrix_construction == "regular":
            return RegularLDPC([factor, factor, num_ones_per_row], "populate-rows")

        elif submatrix_construction == "quasi-cyclic":

            qc_graph = make_graph(factor, factor, factor)

            first_row_indices = random.sample(range(factor), num_ones_per_row)
            qc_graph = construct_cyclic_submatrix(first_row_indices, qc_graph)

            return qc_graph

        elif submatrix_construction == "permuted-quasi-cyclic":

            graph = make_graph(factor, factor, factor)

            first_row_indices = list(range(num_ones_per_row))
            graph = construct_cyclic_submatrix(first_row_indices, graph)

            graph.permute_rows()
            graph.permute_columns()

            return graph
        else:
            raise RuntimeError('Invalid construction method')

'''
Constructs a submatrix graph from a series of right shifts of an originating index list. This method provides the
base implementation for the quasi-cyclic and permuted-quasi-cyclic constructions.
'''
# parameters:
#   first_row_indices: list(int), the indices on which the right shift cycle is to initiate upon
#   graph: TannerGraph, the graph to build the cycles on
# return:
#   TannerGraph, graph: the graph argument is returned after construction
def construct_cyclic_submatrix(first_row_indices, graph):
    for i in range(graph.width):
        new = first_row_indices.copy()
        graph.put(i, new)
        right_shift_row(new, graph.width)
        first_row_indices = new
    return graph
