# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 00:29:00 2020

@author: Subhranil and Anubhab
"""
def validate_input(num_nodes, neighbours):
    """
    Validates all the inputs to be in range
    num_nodes: total number of nodes in the network
    neighbours: the network itself
    init: the probable initiator
    """
    for i in neighbours:
        for j in i:
            if j >= num_nodes or j < 0:
                print("[Error] Invalid node %d!" % (j + 1))
                return False
    return True

def validate_initiator(num_nodes, init):
    """
    Validates the initiator to be in range
    Parameters
    ----------
    init : integer
        The probable initiator node.
    num_nodes: integer
        Total number of nodes in the network.
    Returns
    -------
    bool
        True if init is valid initiator, false otherwise.

    """
    if init >= num_nodes or init < 0:
        print("[Error] Invalid initiator %d!" % (init + 1))
        return False
    return True

def node_to_idx(s):
    """
    While taking input from the user, we use 1 based indexing.
    However, internally 0 based indexing is used everywhere.
    This method converts the argument to int, and decrements
    it by 1 to use internally as a direct index.
    """
    return int(s) - 1

"""
We take input in the following form:
First line contains an integer N, which denotes the number
of nodes in the network. Next N lines contains the neighbours
of node N, in the range 1..N.
Last line contains the initiator I.
Example:
4   # 4 nodes
2 3 # neighbours of node 1
3   # neighbours of node 2
4 1 # neighbours of node 3
1   # neighbours of node 4
1   # initiator
Initiator is always taken as an input from stdin, even when the
network is loaded from a file.
"""

def load_data_from_stdin():
    """
    Reads the input from the stdin.
    This method is almost identical to load_data_from_file,
    except here explicit prompts are printed to stdout.
    """
    # total number of nodes in the network
    num_nodes = int(input("Enter number of nodes in the network: "))
    # the network matrix
    neighbours = []
    for i in range(num_nodes):
        # for each node, we take input in the form
        # a b c d
        # We first strip any whitespaces, and then space
        # split the line
        n = input("Enter neighbours for node %d: " % (i + 1)).strip().split(" ")
        # Now we convert 1 based input string indices
        # to 0 based integer indices
        n = list(map(node_to_idx, n))
        # add the neighbour list of this node to the network
        neighbours.append(n)

    return (num_nodes, neighbours)

def load_data_from_file(file):
    """
    Reads input from the given file.
    Performs exact same actions as load_data_from_stdin.
    Prints error if file is inaccessible.
    """
    with open(file, "r") as f:
        num_nodes = int(f.readline().strip())
        neighbours = []
        for i in range(num_nodes):
            n = list(map(node_to_idx, f.readline().strip().split(" ")))
            neighbours.append(n)

        return (num_nodes, neighbours)
    print("[Error] Unable to read file!")
    return None

import sys

def check_reachability(neighbours, init):
    """
    Performs a BFS on the neighbours list to check reachability
    of all other nodes from the given initiator.
    """
    visited = [False] * len(neighbours)
    queued = [False] * len(neighbours)
    queue = [init]
    queued[init] = True
    for pending in queue:
        visited[pending] = True
        # from the neighbours of present node, extend the queue with
        # such nodes which are not yet visited, and not yet in the queue
        for x in neighbours[pending]:
            if not visited[x] and not queued[x]:
                queue.append(x)
                queued[x] = True
    return [all(visited), init]

def main():
    if len(sys.argv) == 1:
        res = load_data_from_stdin()
    else:
        res = load_data_from_file(sys.argv[1])
    if res is None:
        return
    if not validate_input(*res):
        return
    num_nodes, neighbours = res
    # the initiator
    init = node_to_idx(input("Enter the possible initiator: "))
    if not validate_initiator(num_nodes, init):
        return
    if check_reachability(neighbours, init)[0]:
        print("Node %d can be an initiator!" % (init + 1))
    else:
        print("Node %d cannot be an initator!" % (init + 1))

if __name__ == "__main__":
    main()
