# -*- coding: utf-8 -*-
"""
Created on Thu Dec 31 19:41:46 2020
"""
from time import sleep
from multiprocessing import Pool, Process, Manager
import random
from itertools import repeat

# time spent in critical section, in seconds
SLEEP_TIME = 0.5
# interval to print the status of the nodes
UPDATE_TIME = 0.3

FREE = 0
REQUESTING = 1
EXECUTING = 2

class Node:

    def __init__(self, manager, id_, nodes, parent_id):
        self.id_ = manager.Value('i', id_)
        self.queue_lock = manager.Lock()
        self.queue = manager.list()
        self.nodes = nodes
        self.parent = manager.Value('i', parent_id)
        self.semaphore = manager.Semaphore(0)
        self.status = manager.Value('i', FREE)
        self.status_lock = manager.Lock()
        self.my_requests = 0

    def tick(self, max_req):  # main event loop
        """
        Local clock progression causing random request generation.

        Parameters
        ----------
        max_req : int
            Maximum number of requests after which the program terminates.

        Returns
        -------
        None.

        """
        while self.my_requests < max_req:
            # sleep for random interval of time
            sleep(random.random())
            sleep(random.random())
            sleep(random.random())
            # randomly decide whether to request
            maycall = random.randint(0, 2)
            if maycall:
                self.request()
                self.my_requests += 1

    def request(self):
        """
        Makes a new request. Enters Critical Section if it is root or
        waits till parent gives grant.

        Returns
        -------
        None.

        """
        #print(self, "requesting..")
        self.grant(self)

    def process_queue(self):
        #print(self, "processing queue")
        node = None
        with self.queue_lock:
            if len(self.queue) > 0:
                node = self.queue.pop(0)
                # we perform the checking outside of
                # the queue lock, because when we are
                # awaiting for a node to give us
                # back the control, we allow everybody
                # else to use request for control to us
        if node == None: # if we don't have anyone on the queue, great
            return
        # otherwise check if we have a parent, and request for its permission
        parent = None
        with self.status_lock:
            if self.parent.value != -1:
                parent = self.nodes[self.parent.value]
        if parent != None:
            parent.grant(self)
            self.semaphore.acquire()
            #print(self, "released by", self.parent.value)
        # make the node its parent, i.e. reverse the edge to make child new root
        if node.id_.value == self.id_.value:
            #print(self, "executing cs")
            self.critical_section()
            #print(self, "cs complete")
        else:
            with self.status_lock:
                self.parent.value = node.id_.value
            # release the node's semaphore to allow
            # it to execute critical section
            #print(self, "releasing", node)
            node.semaphore.release()
        self.process_queue()

    def grant(self, node):
        """
        Give access to requesting child or adds it to queue for permitting later.

        Parameters
        ----------
        node : Node
            Reference to the node which is requesting token access.

        Returns
        -------
        None.

        """
        # we use this variable to wait for grant
        # outside of all locks, so they can be
        # acquired by other processes
        #print(self, "asked by", node)
        with self.queue_lock:
            # add the node to our queue
            self.queue.append(node)
        with self.status_lock:
            if self.status.value == EXECUTING:
                return
        self.process_queue()

    def critical_section(self):
        with self.status_lock:
            self.status.value = EXECUTING
            self.parent.value = -1
        sleep(SLEEP_TIME)
        #print(self, "awake")
        with self.status_lock:
            self.status.value = FREE

    def get_status(self):
        """
        Retrieves the status of the node

        Returns
        -------
        int
            execution status of the node.
        int
            current parent of the node.
        String
            Current request_queue of the node.

        """
        return (self.status.value, self.parent.value)#, list(self.queue.queue))

    def __repr__(self):
        return "[Node %d]" % self.id_.value

# queries and prints the status of all the neighbors
def print_status(neighbors):
    STATUS_TEXT = ["free", "Waiting", "IN CRITICAL SECTION"]
    while True:
        i = 0
        for neighbor in neighbors:
            stat = neighbor.get_status()
            #print("Node %2d: %20s (child of: Node %2d) (current queue: %30s)" %
            #      (i, STATUS_TEXT[stat[0]], stat[1], ' '.join(stat[2])))
            print("Node %2d: %20s (child of: Node %2d)" %
                  (i, STATUS_TEXT[stat[0]], stat[1]))
            i += 1
        print()
        sleep(UPDATE_TIME)

def start_tick(neighbors, node, max_req):
    """
    Initiates the free -> request -> cs tick loop for
    each of the nodes

    Parameters
    ----------
    neighbors : Node array
        Array of all the nodes in the graph.
    node : TYPE
        DESCRIPTION.
    max_req : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    neighbors[node].tick(max_req)

def main():
    import sys
    try:
        num_nodes = int(sys.argv[1])
        if num_nodes < 2:
            raise Exception("error")
    except:
        print("[Error] Invalid number of nodes passed as argument!")
        return

    # mp manager to acquire shared locks
    manager = Manager()

    # initialization of all the neighbors
    neighbors = []
    parent_ids = [] # list of parents
    for i in range(num_nodes):
        parent_id = random.randint(0, num_nodes - 1)
        # check if whoever we chose as parent has chosen us
        # as parent or not to avoid cycle
        #while len(neighbors) > parent_id and parent_ids[parent_id] == i:
            #parent_id = random.randint(0, num_nodes - 1)
        neighbors.append(Node(manager, i, neighbors, i-1))
        parent_ids.append(parent_id)

    # the nodes stop after this many total requests are made
    max_req = num_nodes * 3

    # printer process initiation
    # the printer process is independent from the worker
    # pool which manages the nodes. it wakes up at UPDATE_TIME
    # interval, queries and prints the statuses of all the
    # nodes, and sleeps again
    printer = Process(target=print_status, args=(neighbors,), daemon=True)
    printer.start()

    # the worker pool
    # it contains one process for each of the node in the
    # network. each process gets assigned to perform the
    # free -> request -> cs loop for one node.
    jobPool = Pool(processes=len(neighbors))
    jobPool.starmap(start_tick, zip(repeat(neighbors), range(len(neighbors)), repeat(max_req)))


if __name__ == "__main__":
    main()
