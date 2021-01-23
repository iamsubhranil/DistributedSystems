from multiprocessing import Pool, Manager
import random

SLEEP_TIME = 0.3

class Node:

    def __init__(self, manager, l):
        self.left = l
        self.queue = manager.Queue()
        # 1 denotes the _presence_ of the token,
        # i.e. the process is in its cs
        self.token = manager.Value('i', 0)
        self.token_lock = manager.Semaphore()

    def mayrequest(self):
        while True:
            sleep(random.random())
            sleep(random.random())
            if random.randint(0, 1) == 1:
                self.request()

    def request(self):
        with self.token_lock:
            # if we're already in the cs, bail
            if self.token.value == 1:
                return
        self.left.queue.put(self)

    def cs(self):
        with self.token_lock:
            self.token.value = 1
        sleep(SLEEP_TIME)
        with self.token_lock:
            self.token.value = 0

    def process_queue(self):
        while True:
            node = self.queue.get()
            if node == self:
                self.cs()
            else:
                self.left.queue.put(node)


def init_processing(node):
    node.process_queue()

def init_request(node):
    node.mayrequest()

def main():
    num_nodes = 10
    manager = Manager()
    network = [Node(manager, None)]
    for i in range(num_nodes - 1):
        network.append(Node(manager, network[-1]))
    network[0].left = network[-1]
