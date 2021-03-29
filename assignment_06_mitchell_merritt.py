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
        self.id_ = i
        self.acquired_by = None
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
        node.print("Trying to acquire R" + str(self.id_),
                   "[Currently acquired by " + str(self.acquired_by) + "]")
        with self.lock:
            if self.acquired_by == None:
                self.acquired_by = node
                self.sem.release()
                return
        self.acquired_by.grant(node)

    def access(self, node):
        self.sem.acquire()
        node.print("Acquired R" + str(self.id_))
        self.acquired_by = node

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
            self.acquired_by.print("Released R" + str(self.id_))
            self.acquired_by = None
            self.sem.release()

class Node:

    def __init__(self, id, manager):

        self.id = id
        self.u = manager.Value('i',0)
        self.v = 0
        self.blocking = manager.List()
        self.status_lock = manager.Lock()

    def fire(self, max_req, global_sema):
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
        global_sema.release()  # Release semaphore if current node has reached maximum requests


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
        self.print("Resource list generated:", self.get_remaining_resources(resources))
        for res in resources:
            self.resource_semaphores[res].acquire(self)
        for res in resources:
            self.global_resource_list[res].access()
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
        print("[Node %3d] " % self.id_, *args)

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
        for r in resources:
            self.resource_list[r].release(self)
        with self.status_lock:
            self.blocking.clear()

    def grant(self, node):
        with self.status_lock:
            self.blocking.append(node)
        node.transmit(self.u.value, True)

    def transmit(self, val, initial=False):
        with self.status_lock:
            if not initial:
                # if this is not the initial transmission, we check if
                # our u and v values match, and that is equal to val.
                # if it is, then we were the one who started the transmission,
                # and is being asked to retransmit by someone else in
                # the network, thereby ensuring a cycle
                if self.u.value == self.v.value and self.u.value == val:
                    print("DEADLOCK")
                    sys.exit(1)
                else:
                    self.u.value = val
            else:
                # we are starting the transmission
                self.u.value = max(self.u.value, val) + 1
                self.v.value = self.u.value
                val = self.u.value
        # transmit to all nodes which are blocked by current node
        for node in self.blocking:
            node.transmit(val)


def main():

    m = Manager()
    global_sema = m.Semaphore(0)
