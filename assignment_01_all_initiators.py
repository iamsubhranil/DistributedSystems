# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 00:29:00 2020

@author: Subhranil and Anubhab
"""
import sys
import time
import concurrent.futures
import assignment_01_initiator_selection as initiator

def main():
    # load the data
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

    # create a process pool to execute initiator selection
    # tasks in parallel
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # submit all the selection tasks at once to the pool.
        # the pool will submit each selection task to one
        # process and reuse the process when it's done.
        # returned futures will contain the result of the tasks
        # when they are done.
        futureObjects = [executor.submit(initiator.check_reachability, neighbours, init) for init in range(num_nodes)]

        # for all the selection tasks, check if the result is
        # already arrived. if it is, print it.
        # this loop will continue until there is at least one
        # future which is not yet done.
        for f in concurrent.futures.as_completed(futureObjects):
            if f.result() is not None: # check if the result is arrived
                node_checked = f.result()
                if node_checked[0]:
                    print("Node %d can be an initiator!" % (node_checked[1] + 1))
                    count = count + 1

        # print the number of initiators
        if count < 1:
            print("The graph has no initiators!")
        else:
            print(f'The graph has {count} initiators!')


if __name__ == "__main__":
    start = time.perf_counter()
    main()
    finish = time.perf_counter()
    print(f'Finished in {round(finish-start, 2)} seconds')
