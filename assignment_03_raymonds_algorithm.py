from multiprocessing import Pool, Manager
import random

SLEEP_TIME = 0.5

FREE = 0
WAITING = 1
EXECUTING = 2

class Node:

    def __init__(self, manager, id_, nodes, parent_id):
        self.id_ = manager.Value('i', id_)
        self.queue_lock = manager.Lock()
        self.queue = manager.Queue()
        self.parent = nodes[parent_id]
        self.semaphore = manager.Semaphore(0)
        self.status = manager.Value('i', FREE)
        self.status_lock = manager.Lock()

    def tick(self, max_ts):  # main event loop
        while self.ts.value < max_ts:
            # sleep for random interval of time
            sleep(random.random())
            sleep(random.random())
            sleep(random.random())
            # randomly decide whether to request
            maycall = random.randint(0, 2)
            if maycall:
                self.request()

    def request(self):
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
                    if not self.queue.empty():
                        node = self.queue.get()
                # we perform the checking outside of
                # the queue lock, because when we are
                # awaiting for a node to give us
                # back the control, we allow everybody
                # else to use request for control to us

                if node == None: # if we don't have anyone on the queue, great
                    break
                # otherwise
                # make the node its parent
                self.parent = node
                # release the node's semaphore to allow
                # it to execute critical section
                node.semaphore.release()
                # put itself in requesting node's queue
                node.grant(self)
                # wait for the node to finish
                self.semaphore.acquire()

    def grant(self, node):
        # we use this variable to wait for grant
        # outside of all locks, so they can be
        # acquired by other processes
        requested = False
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
                        self.queue.put(node)
                        # if this is the first node, add us to the
                        # parent's queue
                        if self.queue.qsize() == 1:
                            self.parent.grant(self)
                            # mark ourselves as requesting.
                            # we only make request to the parent
                            # once.
                            requesting = True
            else:
                # we're executing, so add and we're done
                with self.queue_lock:
                    # add the node to our queue
                    self.queue.put(node)
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



# initiates the free -> request -> cs tick loop for
# each of the node
def start_tick(neighbors, node, max_req):
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
        while len(neighbors) > parent_id and parent_ids[parent_id] == i:
            parent_id = random.randint(0, num_nodes - 1)
        neighbors.append(Node(manager, i, neighbors, parent_id))
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
