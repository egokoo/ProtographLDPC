import random

from libs.TannerGraph import *

'''
- A class for the handling of Regular LDPC matrices in tanner graph form

The tanner graph is stored as a dictionary, row indices (check nodes) are mapped to lists of column indices (variable
nodes) to indicate bipartite connections

args: input to enable construction. input follows the following construction patern: h = n * (c / r) where c / r is not
explicitly simplified, h = height of matrix, n = length of codeword/width matrix, c = column weight, r = row weight
where weightages are constant for the most part (certain constructions fail to provide complete regularity)

construction specifies the method by which the matrix corresponding to args will be created
'''


class RegularLDPC(TannerGraph):

    # parameters:
    #   args: list of arguments needed for regular ldpc construction
    #   construction: the type of construction to be used
    # return:
    #   a fully defined Regular LDPC code
    def __init__(self, args, construction, verbose=False):
        TannerGraph.__init__(self, args, construction=construction)

        self.width = int(self.args[0])

        #
        # args provided [width (n_bits), height (n_checks), 1s per col]
        # user-controlled matrix weightages
        #
        # Because r is dependent on width, height, and c (assuming regularity), defining c results
        # in limiting the constructor to one possible r value.
        # The resulting n, c, r values are passed to the constructor.
        #
        if len(self.args) == 3:
            self.height = int(self.args[1])
            self.n = int(self.args[0])
            self.c = int(self.args[2])
            self.r = int((self.width / self.height) * self.c)
            if verbose:
                print("INFO: Regular code: inferred ones per row as", self.r)
        else:
            raise RuntimeError("invalid input provided")

        self.tanner_graph = RegularLDPC.get_parity_check_graph(self.n, self.r, self.c, self.construction)

    # parameters:
    #   n: int, the width of the LDPC code, the codeword length
    #   r: int, the weight of each row of the LDPC code
    #   c: int, the weight of each column of the code
    #   method: String, the construction to be employed
    @staticmethod
    def get_parity_check_graph(n, r, c, method):

        # Gallager's construction of random LDPC matrices
        # although this construction yields perfectly regular codes, it is not a reliable construction:
        #   it is impossible to enforce regularity while strictly maintaining a provided height and width
        if method == "gallager":

            if n % r != 0:
                print("WARNING: Gallager construction: "+
                    "cannot generate perfectly regular matrix for the given arguments, modifications inferred")

            # keeps track of all created submatrices
            submatrices = []
            for i in range(c):
                # creates random submatrix, appends it to list
                submatrices.append(SubGraph(n, r))

            # merges all matrices in submatrices for final ldpc matrix
            return RegularLDPC.merge(submatrices, n, r)

        # ------------------------------------------
        # Duplicate code included for easier reading
        # ------------------------------------------

        # enforces constant row weight
        elif method == "populate-rows":

            # constructs initial empty parity check matrix
            tanner_graph = {}
            for i in range(int(n * c / r)):
                tanner_graph[i] = []

            width = n
            height = int(n * c / r)

            # all possible 1s locations (index in column)
            available_indices = []

            k = n * c
            for i in range(k - 1, -1, -1):
                # fills available indices with column indices
                available_indices.append(i % width)

            placed_entries = 0
            for i in range(height):
                for j in range(r):

                    # loops through all index positions in available indices, stops when the row does not contain a 1 at
                    # a specified index
                    l = 0
                    while l < len(available_indices) and tanner_graph.get(i).count(available_indices[l]) == 1:
                        l += 1

                    # if all entries have been placed
                    if l + placed_entries == k:

                        # choose a random column index and populate the matrix at that location
                        random_index = random.choice(range(width))
                        while tanner_graph.get(i).count(random_index) == 1:
                            random_index = random.choice(range(width))

                        tanner_graph.get(i).append(random_index)

                    # if not all entries have been placed
                    else:

                        # choose a random column index
                        random_index = random.choice(range(len(available_indices)))
                        while tanner_graph.get(i).count(available_indices[random_index]) != 0 and len(
                                available_indices) > 1:
                            random_index = random.choice(range(len(available_indices)))

                        # populate the matrix at specified location
                        tanner_graph.get(i).append(available_indices.pop(random_index))
                        placed_entries += 1

            return tanner_graph

        # enforces constant column weight
        elif method == "populate-columns":

            # create the initial empty graph
            tanner_graph = {}
            for i in range(n):
                tanner_graph[i] = []

            width = n
            height = int(n * c / r)

            # contains all the possible indices for population
            available_indices = []

            k = n * c
            for i in range(k - 1, -1, -1):
                # fills available indices with row indices
                available_indices.append(i % height)

            placed_entries = 0
            for i in range(width):
                for j in range(c):

                    # loops through available entries to find an index that is not already populated
                    l = 0
                    while l < len(available_indices) and tanner_graph.get(i).count(available_indices[l]) == 1:
                        l += 1

                    # if all entries have been placed
                    if placed_entries + l == k:

                        # choose a random row index, not restrained by available indices
                        random_index = random.choice(range(height))
                        while tanner_graph.get(i).count(random_index) == 1:
                            random_index = random.choice(range(height))

                        # populate matrix at that location
                        tanner_graph.get(i).append(random_index)

                    # if not all 1s have been placed
                    else:

                        # choose a random available index
                        random_index = random.choice(range(len(available_indices)))
                        while tanner_graph.get(i).count(available_indices[random_index]) != 0 and len(
                                available_indices) > 1:
                            random_index = random.choice(range(len(available_indices)))

                        # populate matrix at that location
                        tanner_graph.get(i).append(available_indices.pop(random_index))
                        placed_entries += 1

            return transpose(tanner_graph, height)
        else:
            raise RuntimeError('Invalid construction method')

    '''
    as part of the Gallager construction, this function stacks all the generated submatrices vertically
    (in this case sub graphs). Because of the nature of LDPC codes, the order of the stacking is irrelevant,
    and subsequently random
    '''
    # parameters:
    #   submatrices: list of TannerGraph.tanner_graph, a list of dictionaries to be stacked
    #   n: int, the width of each codeword
    #   r: int, the weight of each row of each submatrix in submatrices
    # return:
    #   a TannerGraph.tanner_graph dictionary containing the entire code constructed from individual submatrices
    @staticmethod
    def merge(submatrices, n, r):
        merged = {}
        for i in range(len(submatrices)):
            for j in range(int(n / r)):
                merged[int(i * n / r + j)] = submatrices[i].map[j]
        return merged


# the equivalent of the submatrix in Gallager's construction, used only for Gallager's construction
class SubGraph:

    # parameters:
    #   n: int, the width of the cumulative code
    #   r: int, the weight of each row in the cumulative code
    def __init__(self, n, r):

        # creates graph with appropriate no. check nodes
        self.map = {}
        for i in range(int(n / r)):
            self.map[i] = []

        # defines all possible indices, randomizes for sparse parity-codeword mapping
        codeword_indices = list(range(0, n))
        random.shuffle(codeword_indices)

        # assigns codeword bits to parity check equations
        for i in range(int(n / r)):
            for j in range(int(r)):
                self.map[i].append(codeword_indices[i * r + j])

    def __repr__(self):
        return str(self.map)
