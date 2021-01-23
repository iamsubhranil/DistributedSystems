from multiprocessing import Pool, Process, Manager
from time import sleep
import random
from itertools import repeat

SLEEP_TIME = 0.3
# interval to print the status of the nodes
UPDATE_TIME = 0.3

class Node:

    def __init__(self, id_, manager, l):
        self.id_ = manager.Value('i', id_)
        self.left = l
        self.queue = manager.Queue()
        # 1 denotes the _presence_ of the token,
        # i.e. the process is in its cs
        # 2 denotes the process is requesting
        self.token = manager.Value('i', 0)
        self.token_lock = manager.Semaphore()
        self.my_requests = 0
        self.dummy_queue = manager.list()

    def mayrequest(self, max_req):
        while self.my_requests < max_req:
            # sleep for random interval of time
            sleep(random.random())
            sleep(random.random())
            if random.randint(0, 1) == 1:
                self.request()
                self.my_requests += 1

    def request(self):
        with self.token_lock:
            # if we're already in the cs, bail
            if self.token.value == 1 or self.token.value == 2:
                return
            else:
                self.token.value = 2
        self.left.queue.put(self.id_)
        self.left.dummy_queue.append(self.id_.value)
        print("Requesting - ", self.id_.value)

    def cs(self):
        with self.token_lock:
            self.token.value = 1
        sleep(SLEEP_TIME)
        with self.token_lock:
            self.token.value = 0

    def process_queue(self):
        if self.queue.qsize() == 0:
            return
        node = self.queue.get()
        self.dummy_queue.pop(0)
        print("Before Processing ... ", node)
        if node.value == self.id_.value:
            print("Processing ...  %d", node.value)
            self.cs()
        else:
            while True:
                self.left.queue.put(node)
                self.left.dummy_queue.insert(0, node.value)
                if (self.queue.qsize() == 0):
                    break
                node = self.queue.get()
                self.dummy_queue.pop(0)

    def get_status(self):
        return (self.id_.value, self.token.value, self.dummy_queue)


def init_processing(network, node):
    network[node].process_queue()

def init_request(network, node, max_req):
    network[node].mayrequest(max_req)

# queries and prints the status of all the neighbors
def print_status(neighbors):
    STATUS_TEXT = ["FREE", "IN CRITICAL SECTION", "Requesting"]
    while True:
        i = 0
        for neighbor in neighbors:
            stat = neighbor.get_status()
            print("Node %2d:      Status = %20s" %
                  (stat[0], STATUS_TEXT[stat[1]]),end='\t')
            print("Queue = ",stat[2])
            i += 1
        print()
        sleep(UPDATE_TIME)

def main():
    num_nodes = 3
    manager = Manager()
    network = [Node(0,manager, None)]
    for i in range(num_nodes - 1):
        network.append(Node(i+1, manager, network[-1]))
    network[0].left = network[-1]

    # the nodes stop after this many total requests are made
    max_req = num_nodes

    printer = Process(target=print_status, args=(network,), daemon=True)
    printer.start()




    # the worker pool
    # it contains one process for each of the node in the
    # network.
    jobPool = Pool(processes=len(network))
    jobPool.starmap(init_request, zip(repeat(network), range(len(network)), repeat(max_req)))
    jobPool.close()
    jobPool.join()

    processes = []
    for i in range(num_nodes):
        processes.append(Process(target=init_processing, args=(network, i), daemon=True))
        processes[-1].start()

    for p in processes:
        p.join()


if __name__ == "__main__":
    main()
