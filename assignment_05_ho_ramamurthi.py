"""
Created on Sun Feb 21 19:41:46 2021

@author: Subhranil, Anubhab
"""
from time import sleep
from multiprocessing import Pool, Process, Manager
import random
from itertools import repeat
import sys
import signal

CONTROLLER_SLEEP = 0.2

class Node:

    def __init__(self, id_, res_tab, res_tab_lock, num_res, res_sems):
        # resource table is (resource x process) bipolar table where
        # -1 in a cell denotes resource Ri is being waited on by process
        # Pj. +1 denotes it is acquired by Pj. This is a global table,
        # and is accessed and modified by all the nodes in the network.
        self.resource_table = res_tab
        # lock for the table
        self.res_tab_lock = res_tab_lock
        self.id_ = id_
        self.num_resource = num_res
        # semaphores for the nodes to wait on resources
        self.resource_semaphores = res_sems
        self.my_requests = 0
        self.die = False

    def fire(self, max_req):
        while self.my_requests < max_req and not self.die:
            if random.randint(0, 1) == 1:
                self.request()
                self.my_requests += 1

            sleep(random.random())
            sleep(random.random())
            sleep(random.random())

    def request(self):
        num_res = random.randint(1, self.num_resource)
        resources = random.sample(range(self.num_resource), num_res)
        sleep_time = random.random()
        with self.res_tab_lock:
            for res in resources:
                self.resource_table[res][self.id_] = -1
        for res in resources:
            self.print("Waiting for R" + str(res) + "..")
            self.resource_semaphores[res].acquire()
            self.print("  Acquired  R" + str(res) + "..")
            with self.res_tab_lock:
                self.resource_table[res][self.id_] = 1

        sleep_time = 0.2
        self.execute(resources, sleep_time)

    def print(self, *args):
        print("[Node %3d] " % self.id_, *args)

    def execute(self, resources, sleep_time):
        sleep(sleep_time)
        for res in resources:
            with self.res_tab_lock:
                self.resource_table[res][self.id_] = 0
            self.print("  Released  R" + str(res) + "..")
            self.resource_semaphores[res].release()

def fire_node(nodes, num, max_req):
    nodes[num].fire(max_req)

def print_path(path, vertex, visited=set()):
    if path[vertex] == -1:
        print(vertex, end=' ')
    else:
        if vertex not in visited:
            visited.add(vertex)
            print_path(path, path[vertex], visited)
            print("-->", end=' ')
        print(vertex, end=' ')

def dfs(adj, vertex, unvisited, path, stack=[]):
    #print("at", vertex)
    if vertex in unvisited:
        unvisited.remove(vertex)
    if vertex in stack:
        return False, vertex
    stack.append(vertex)
    for v in adj[vertex]:
        path[v] = vertex
        res, v = dfs(adj, v, unvisited, path, stack)
        if not res:
            return res, v
    stack.pop()
    return True, None

def check_for_deadlock(res_tab, res_tab_lock, num_nodes, killEvent):
    while True:
        print("[Controller] Starting deadlock detection..")
        adjacency_matrix = [[] for _ in range(num_nodes)]
        with res_tab_lock:
            for row in res_tab:
                to_vertex = [idx for idx in range(num_nodes) if row[idx] == 1]
                if len(to_vertex) == 0:
                    continue
                to_vertex = to_vertex[0]
                from_vertices = [idx for idx in range(num_nodes) if row[idx] == -1]
                for v in from_vertices:
                    if to_vertex not in adjacency_matrix[v]:
                        adjacency_matrix[v].append(to_vertex)
        # print(adjacency_matrix)
        # dfs
        unvisited = list(range(num_nodes))
        cycle = False
        path, last_vertex = None, None
        while not cycle and len(unvisited) > 0:
            u = unvisited.pop(0)
            path = [-1] * num_nodes
            c, last_vertex = dfs(adjacency_matrix, u, unvisited, path)
            cycle = cycle or not c
        if cycle:
            print("[Controller] Deadlock detected! System is UNSAFE!")
            print("[Controller] The cycle is: ")
            #print(path)
            print_path(path, last_vertex)
            print()
            killEvent.set()
            return
        else:
            print("[Controller] No deadlock detected!")
        sleep(CONTROLLER_SLEEP)

def main():
    if len(sys.argv) < 3:
        print("Usage:", sys.argv[0], "num_process", "num_resource")
        return
    m = Manager()
    num_process = int(sys.argv[1])
    num_resource = int(sys.argv[2])
    res_tab = [m.list([0] * num_process) for _ in range(num_resource)]
    res_tab = m.list(res_tab)
    res_tab_lock = m.Lock()
    res_sems = m.list([m.Semaphore() for _ in range(num_resource)])
    nodes = [Node(i, res_tab, res_tab_lock, num_resource, res_sems) for i in range(num_process)]

    # the nodes stop after this many total requests are made
    max_req = num_process/2

    killEvent = m.Event()
    # controller process
    controller = Process(target=check_for_deadlock, args=(res_tab, res_tab_lock, num_process, killEvent), daemon=True)
    controller.start()

    '''
    processes = []
    for i in range(num_process):
        processes.append(Process(target=check_for_deadlock, args=(), daemon=True))
        processes[-1].start()
        '''
    # the worker pool
    # it contains one process for each of the node in the
    # network. each process gets assigned to perform the
    # free -> request -> cs loop for one node.
    jobPool = Pool(processes=len(nodes))
    jobPool.starmap_async(fire_node, zip(repeat(nodes), range(len(nodes)), repeat(max_req)))
    #jobPool.close()
    # request done

    killEvent.wait()
    jobPool.terminate()
    controller.join()
    controller.close()
    #controller.join()

    '''
    for node in nodes:
        with node.queue_lock:
            node.queue.put((None, SENTINEL))
            node.dummy_queue.append(SENTINEL)


    for p in processes:
        p.join()
        '''
if __name__ == "__main__":
    main()
