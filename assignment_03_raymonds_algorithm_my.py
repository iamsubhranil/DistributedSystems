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
WAITING = 1
EXECUTING = 2

class Node:

    def __init__(self, manager, id_, nodes, parent_id):
        self.id_ = manager.Value('i', id_)
        self.queue_lock = manager.Lock()
        self.queue = manager.list()
        if parent_id > 0:
            self.parent = nodes[parent_id]
        else:
            self.parent = None
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
        print(self, "requesting..")
        self.queue.append(self)  # Add own id in own local queue
        # if we don't have a parent, fine
        if self.parent == None:
            self.critical_section()
        else:
            self.parent.grant(self)
            self.semaphore.acquire()
            self.critical_section()
            # we will not be able to generate
            # new requests until we have served
            # everyone who is waiting in the queue
        while True:
            node = None
            with self.queue_lock:
                if not len(self.queue) == 0:
                    node = self.queue.pop(0)
                    if node.id_ == self.id_:
                        continue
            # we perform the checking outside of
            # the queue lock, because when we are
            # awaiting for a node to give us
            # back the control, we allow everybody
            # else to use request for control to us

            if node == None: # if we don't have anyone on the queue, great
                break
            # otherwise
            # make the node its parent, i.e. reverse the edge to make child new root
            self.parent = node
            # release the node's semaphore to allow
            # it to execute critical section
            node.semaphore.release()
            # put itself in requesting node's queue
            node.grant(self)
            # wait for the node to finish
            self.semaphore.acquire()

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
        requesting = False
        with self.status_lock:
            if self.status == FREE:
                if self.parent == None:
                    # if we don't have a parent AND we're doing nothing,
                    # we cool
                    node.semaphore.release()
                else:
                    # we're doing nothing, but we have a parent
                    with self.queue_lock:
                        # add the node to our queue
                        self.queue.append(node)
                        # if this is the first node, add us to the
                        # parent's queue
                        if len(self.queue) == 1:
                            self.parent.grant(self)
                            # mark ourselves as requesting.
                            # we only make request to the parent
                            # once.
                            requesting = True
            else:
                # we're executing, so add and we're done
                with self.queue_lock:
                    # add the node to our queue
                    self.queue.append(node)
        if requesting:
            # if we're requesting for a parent's grant, we wait
            self.semaphore.acquire()

    def critical_section(self):
        with self.status_lock:
            self.status = EXECUTING
            self.parent = None
        sleep(SLEEP_TIME)
        with self.status_lock:
            self.status = FREE

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
        if self.parent:
            return (self.status.value, self.parent.id_.value)#, list(self.queue.queue))
        else:
            return (self.status.value, -1)#, list(self.queue.queue))

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
