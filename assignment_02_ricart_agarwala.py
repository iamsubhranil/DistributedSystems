from time import sleep
from multiprocessing import Pool, Process, Manager
import random
from itertools import repeat


def generate_timestamp(ts_counter):
    ts_counter.set(ts_counter.value + 1)
    return ts_counter.value


SLEEP_TIME = 2
UPDATE_TIME = 0.5


class Node:

    def __init__(self, manager, id_, n, tc):
        # 0 -> not requesting, 1 -> requesting, 2 -> in cs
        self.status = manager.Value('i', 0)
        self.status_lock = manager.Lock()
        self.semaphore = manager.Semaphore(0)
        self.ts = manager.Value('i', 0)
        self.request_queue = manager.Queue()
        self.id_ = id_
        self.neighbors = n
        self.ts_counter = manager.Value('i', 0)

    def tick(self, max_requests):  # main event loop
        while self.ts_counter.value < max_requests:
            sleep(random.random())
            sleep(random.random())
            sleep(random.random())
            maycall = random.randint(0, 2)
            if maycall :
                self.request()

    def request(self):
        with self.status_lock:
            self.status.set(1)  # set the status
        self.ts.set(generate_timestamp(self.ts_counter))  # get a timestamp
        for neighbor in self.neighbors:  # ask for all tokens at once
            if neighbor == self:  # skip self
                continue
            neighbor.grant(self.semaphore, self.ts, self.id_)
        for _ in range(len(self.neighbors) - 1):  # wait until everyone grants
            self.semaphore.acquire()

        # now execute the cs
        self.critical_section()

    def critical_section(self):
        with self.status_lock:
            self.status.set(2)  # set the status
        # critical section
        sleep(SLEEP_TIME)
        # reset the status
        with self.status_lock:
            self.status.set(0)
        # grant all the requests in the queue
        while not self.request_queue.empty():
            self.request_queue.get().release()

    def grant(self, sem, ts, id_):
        with self.status_lock:  # make sure only one thread calls this
            if self.status.value == 0:  # if we are free, we grant
                sem.release()
            elif self.status.value == 1 and self.ts.value > ts.value:
                # if we are busy, we grant only when we are newer
                sem.release()
            elif self.status.value == 1 and self.ts.value == ts.value and self.id_ > id_ :
                # if we are busy and request comes from node with same
                # timestamp, then we grant only if they have smaller id value
                # this is tie-breaking condition which might be unfair
                print(self.id_, id_)
                sem.release()
            else:  # either we're in cs or requesting with a lower ts
                # we put the sem in a queue to be unlocked when
                # we exit from the cs
                self.request_queue.put_nowait(sem)

    def get_status(self):
        return (self.status.value, self.ts.value)


def print_status(neighbors):
    STATUS_TEXT = ["free", "Requesting", "IN CRITICAL SECTION"]
    while True:
        i = 0
        for neighbor in neighbors:
            stat = neighbor.get_status()
            print("Node %d: %s (timestamp: %d,%d)" %
                  (i, STATUS_TEXT[stat[0]], stat[1], i))
            i += 1
        print()
        sleep(UPDATE_TIME)


def start_tick(neighbors, node, max_requests):
    neighbors[node].tick(max_requests)


def main():
    import sys
    try:
        num_nodes = int(sys.argv[1])
    except:
        print("[Error] Invalid number of nodes passed as argument!")
        return

    manager = Manager()
    #ts_lock = manager.Lock()
    ts_counter = manager.Value('i', 0)

    neighbors = []
    for i in range(num_nodes):
        neighbors.append(Node(manager, i, neighbors, ts_counter))

    max_requests = num_nodes*3
    printer = Process(target=print_status, args=(neighbors,), daemon=True)
    printer.start()



    jobPool = Pool(processes=len(neighbors))
    jobPool.starmap(start_tick, zip(repeat(neighbors), range(len(neighbors)), repeat(max_requests)))


if __name__ == "__main__":
    main()
