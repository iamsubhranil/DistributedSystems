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
        self.acquired_by = m.Value('i', -1)


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
                   "[Currently acquired by " + str(self.acquired_by.value) + "]")
        self.sem.acquire()
        self.acquired_by.value = node.id_
        node.print("Acquired R" + str(self.id_))


    def release(self, node):
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
        node.print("Released R" + str(self.id_))
        self.sem.release()



class Node:

    def __init__(self, id, manager):

        self.id = id
        self.u = manager.Value('i',0)
        self.v = 0
        self.u_lock = manager.Lock()
        #self.blocked_by = manager.Value('i',-1)
        self.blocking = manager.List()

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
        with self.res_tab_lock:
            self.print("Resource list generated:", self.get_remaining_resources(resources))
            for res in resources:
                self.resource_table[res][self.id_] = -1  # update resource status table
        i = 0  # number of resources held
        for res in resources:
            self.resource_semaphores[res].acquire(self)
            with self.res_tab_lock:
                self.resource_table[res][self.id_] = 1
            self.print("Remaining", self.get_remaining_resources(resources[i+1:]))
            i += 1
        # All resources accessed, now utilise
        self.execute(resources, sleep_time)


    def grant(self,)

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
        for res in resources:
            with self.res_tab_lock:
                self.resource_table[res][self.id_] = 0
            self.resource_semaphores[res].release(self)

    def get_blocked(self, node, neighbors):

        # current node gets blocked by argument 'node'
        with self.u_lock:
            self.u.value = max(self.u.value,node.u.value) + 1
            self.v.value = self.u.value

        self.blocked_by = node.id.value

        self.transmit(neighbors)  # apply transmit rule after block rule

    def transmit(self, neighbors):

        # check all nodes to find which nodes are blocked by current node
        for node in neighbors:
            if node.blocked_by.value == self.id.value:
                with node.u_lock:
                    node.u.value = self.u.value
                    node.transmit(neighbors)

    def detect(self):

        if self.blocked_by != -1:
            with self.u_lock:
                if self.u.value == self.v.value and self.u.value == self.blocked_by.u.value:
                    # Deadlock
                    pass


def main():

    m = Manager()
    global_sema = m.Semaphore(0)
