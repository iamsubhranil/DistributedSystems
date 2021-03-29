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

class Node:

    def __init__(self, id, manager):

        self.id = id
        self.u = manager.Value('i',0)
        self.v = 0
        self.u_lock = manager.Lock()
        self.blocked_by = manager.Value('i',-1)

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
                    node.u_lock.value = self.u.value
                    node.transmit(neighbors)

    def detect(self):

        if self.blocked_by != -1:
            with self.u_lock:
                if self.u.value == self.v.value and self.u.value == self.blocked_by.u.value:
                    # Deadlock
                    pass


def main():

    manager = Manager()

