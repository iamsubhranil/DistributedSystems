from multiprocessing import Pool, Process, Manager
from time import sleep
import random
from itertools import repeat
import sys

SLEEP_TIME = 0.5
# interval to print the status of the nodes
UPDATE_TIME = 0.3

class Node:

    def __init__(self, id_, manager, l, q, qlock, watch, num_nodes):
        self.id_ = manager.Value('i', id_)
        self.left = l
        self.queue = q # global queue
        self.queue_lock = qlock # global queue lock
        self.watch = watch # semaphore
        self.num_nodes = num_nodes # number of nodes in the network
        # 1 denotes the _presence_ of the token,
        # i.e. the process is in its cs
        # 2 denotes the process is requesting
        self.token = manager.Value('i', 0)
        self.token_lock = manager.Lock()
        self.my_requests = 0

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
        with self.queue_lock:
            self.queue.append(self.id_.value)
            if len(self.queue) == 1:
                for i in range(self.num_nodes):
                    self.watch.release()
        #print("Requesting - ", self.id_.value)

    def cs(self):
        with self.token_lock:
            self.token.value = 1
        sleep(SLEEP_TIME)
        with self.queue_lock:
            self.queue.pop(0) # remove itself from the queue
            for i in range(self.num_nodes):
                self.watch.release() # wake all other threads
        with self.token_lock:
            self.token.value = 0

    def process_queue(self):
        while True:
            self.watch.acquire()
            cs_go = False
            with self.queue_lock:
                if len(self.queue) > 0 and self.queue[0] == self.id_.value:
                    cs_go = True
            #print(self.id_.value, " Before Processing ... ", node)
            if cs_go:
                #print("Processing ...  %d", node.value)
                self.cs()

    def get_status(self):
        return (self.id_.value, self.token.value, self.queue)


def init_processing(network, node):
    network[node].process_queue()

def init_request(network, node, max_req):
    #print("Requesting ", node)
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
            if stat[1] == 1:
                print("Queue = ",stat[2])
            else:
                print("")
            i += 1
        print()
        sleep(UPDATE_TIME)

def main():
    num_nodes = int(sys.argv[1])
    manager = Manager()
    global_queue = manager.list()
    global_lock = manager.Lock()
    global_watch = manager.Semaphore()
    network = [Node(0, manager, None, global_queue, global_lock, global_watch, num_nodes)]
    for i in range(num_nodes - 1):
        network.append(Node(i+1, manager, network[-1], global_queue, global_lock, global_watch, num_nodes))
    network[0].left = network[-1]

    # the nodes stop after this many total requests are made
    max_req = num_nodes

    printer = Process(target=print_status, args=(network,), daemon=True)
    printer.start()


    processes = []
    for i in range(num_nodes):
        processes.append(Process(target=init_processing, args=(network, i), daemon=True))
        #processes.append(Process(target=init_request,
        #                         args=(network, i, max_req),
        #                         daemon=True))
        processes[-1].start()


    # the worker pool
    # it contains one process for each of the node in the
    # network.
    jobPool = Pool(processes=len(network))
    jobPool.starmap(init_request, zip(repeat(network), range(num_nodes), repeat(max_req)))
    jobPool.close()
    jobPool.join()

    for p in processes:
        p.join()


if __name__ == "__main__":
    main()
