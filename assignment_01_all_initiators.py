# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 00:29:00 2020

@author: Anubhab
"""
import sys
import time
import concurrent.futures
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

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futureObjects = [executor.submit(initiator.check_reachability, neighbours, init) for init in range(num_nodes)]

        for f in concurrent.futures.as_completed(futureObjects):
            if (f.result() is not None):
                node_checked = f.result()
                if (node_checked[0]):
                    print("Node %d can be an initiator!" % (node_checked[1] + 1))
                    count = count + 1

        if count < 1:
            print("The graph has no initiators!")
        else:
            print(f'The graph has {count} initiators!')


if __name__ == "__main__":
    start = time.perf_counter()
    main()
    finish = time.perf_counter()
    print(f'Finished in {round(finish-start, 2)} seconds')
