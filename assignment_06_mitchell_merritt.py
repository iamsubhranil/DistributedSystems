# -*- coding: utf-8 -*-
"""
Created on Sat Mar 27 19:41:46 2021

@author: Subhranil, Anubhab
"""
from multiprocessing import Pool, Process, Manager
from time import sleep
import random
from itertools import repeat
import sys

class Resource:

    def __init__(self, m, i):
        self.sem = m.Semaphore()
        self.id_ = m.Value('i', i)
        self.acquired_by = m.list([None]) # we create a shared list to store the node
        self.lock = m.Lock()

    def acquire(self, node):
        """
        Acquires the resource object

        Parameters
        ----------
        node : Node
            Node object requesting for the resource

        Returns
        -------
        None.

        """
        node.print("Trying to acquire R" + str(self.id_.value),
                   "[Currently acquired by " + str(self.acquired_by[0]) + "]")
        with self.lock:
            if self.acquired_by[0] == None:
                self.acquired_by[0] = node
                self.sem.release()
                return
        self.acquired_by[0].grant(node)

    def access(self, node):
        self.sem.acquire()
        with self.lock:
            self.acquired_by[0] = node
            node.print("Acquired R" + str(self.id_.value))

    def release(self):
        """
        Releases the resource object once served

        Parameters
        ----------
        node : Node
            Node object requesting for the resource

        Returns
        -------
        None.

        """
        with self.lock:
            print("here", self.id_.value)
            self.acquired_by[0].print("Released R" + str(self.id_.value))
            self.acquired_by[0] = None
            self.sem.release()

class Node:

    def __init__(self, id_, num_nodes, manager, resource_list, global_sema):

        self.id_ = manager.Value('i', id_)
        self.u = manager.Value('i', 0)
        self.v = manager.Value('i', 0)
        self.blocking = manager.list()
        self.status_lock = manager.Lock()
        self.global_resource_list = resource_list
        self.global_sema = global_sema
        self.my_requests = 0
        self.num_resource = len(resource_list)
        self.num_nodes = num_nodes

    def fire(self, max_req):
        """
        Generate new resource requests

        Parameters
        ----------
        max_req : int
            Maximum number of requests a node can make.
        global_sema : Semaphore
            Semaphore to check if further requests are possible.

        Returns
        -------
        None.

        """
        while self.my_requests < max_req:
            if random.randint(0, 1) == 1:
                self.request()
                self.my_requests += 1

            sleep(random.random())
            sleep(random.random())
            sleep(random.random())
        self.print("Maximum Requests served. Exiting ...")
        self.global_sema.release()  # Release semaphore if current node has reached maximum requests


    def request(self):
        """
        Request resources and utilise them

        Returns
        -------
        None.

        """
        num_res = random.randint(1, self.num_resource)  # number f resources required
        resources = random.sample(range(self.num_resource), num_res)  # which resources are required
        sleep_time = random.random() + random.random()
        self.print("Resource list generated:", resources)
        for res in resources:
            self.global_resource_list[res].acquire(self)
        for res in resources:
            self.global_resource_list[res].access(self)
        # All resources accessed, now utilise
        self.execute(resources, sleep_time)


    def print(self, *args):
        """
        Displays passed information along with id of the node

        Parameters
        ----------
        *args : Pointer
            Variable number of arguments.

        Returns
        -------
        None.

        """
        print("[Node %3d] " % self.id_.value, *args)

    def execute(self, resources, sleep_time):
        """
        Utilise the requested resources

        Parameters
        ----------
        resources : List
            List of all the resources that are requested.
        sleep_time : int
            Time to execute.

        Returns
        -------
        None.

        """
        sleep(sleep_time)
        with self.status_lock:
            for r in resources:
                self.global_resource_list[r].release()
            self.print("Clearing blocking list")
            while len(self.blocking) > 0:
                self.blocking.pop()
        self.print("CS done")

    def grant(self, node):
        with self.status_lock:
            self.blocking.append(node)
        node.transmit(self.u.value, True)

    def transmit(self, val, initial=False, path=[]):
        path.append(self.id_.value)
        with self.status_lock:
            if not initial:
                # if this is not the initial transmission, we check if
                # our u and v values match, and that is equal to val.
                # if it is, then we were the one who started the transmission,
                # and is being asked to retransmit by someone else in
                # the network, thereby ensuring a cycle
                if self.u.value == self.v.value and self.u.value == val:
                    self.print("DEADLOCK ->", path)
                    for _ in range(self.num_nodes):
                        self.global_sema.release()  # release all as no other requests can be granted
                    return
                    #sys.exit(1)
                else:
                    self.u.value = val
            else:
                # we are starting the transmission
                self.u.value = max(self.u.value, val) + 1
                self.v.value = self.u.value
                val = self.u.value
        # transmit to all nodes which are blocked by current node
        for node in self.blocking:
            node.transmit(val, False, path)
        path.pop()

    def __str__(self):
        return "Node %2d" % self.id_.value

def fire_node(nodes, num, max_req):
    """
    Initiates the resource requests for each of the nodes

    Parameters
    ----------
    nodes : List of Nodes
        List of all nodes in the system.
    num : int
        Number of nodes in the system.
    max_req : int
        Maximum number of requests a node can make.
    global_sema : Semaphore
        Semaphore to check if further requests are possible.

    Returns
    -------
    None.

    """
    nodes[num].fire(max_req)


def main():
    if len(sys.argv) < 3:
        print("Usage: %s <num_nodes> <num_resources>" % sys.argv[0])
        return
    m = Manager()
    global_sema = m.Semaphore()
    num_process = int(sys.argv[1])
    num_resource = int(sys.argv[2])
    #global_resource_list = m.list([0] * num_resource)
    #global_res_list_lock = m.Lock()
    global_resource_list = m.list([Resource(m, i) for i in range(num_resource)])

    nodes = [Node(i, num_process, m, global_resource_list, global_sema) for i in range(num_process)]

    # the nodes stop after this many total requests are made
    max_req = num_process * 5

    # the worker pool
    # it contains one process for each of the node in the
    # network. each process gets assigned to perform the
    # free -> request -> cs loop for one node.
    jobPool = Pool(processes=len(nodes))
    jobPool.starmap_async(fire_node, zip(repeat(nodes), range(num_process), repeat(max_req)))

    for _ in range(num_process):
        global_sema.acquire()

    jobPool.terminate()

if __name__ == "__main__":
    main()
