# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 00:29:00 2020

@author: Anubhab
"""
import sys
import assignment_01_initiator_selection as initiator

def main():
    if len(sys.argv) == 1:
        res = initiator.load_data_from_stdin()
    else:
        res = initiator.load_data_from_file(sys.argv[1])
    if res is None:
        return
    if not initiator.validate_input(*res):
        return
    num_nodes, neighbours = res
    count = 0
    for init in range(5):
        if initiator.check_reachability(neighbours, init):
            print("Node %d can be an initiator!" % (init + 1))
            count = count + 1
    if count < 1:
        print("The graph has no initiators!\n")
    else:
        print(f'The graph has {count} initiators!\n')

if __name__ == "__main__":
    main()