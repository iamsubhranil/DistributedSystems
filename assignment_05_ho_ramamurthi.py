from multiprocessing import Pool, Semaphore, Manager
import random

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

    def fire(self):
        while True:
            if random.randint(0, 1) == 1:
                self.request()

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
            self.resource_semaphores[res].acquire()
            with self.res_tab_lock:
                self.resource_table[res][self.id_] = 1

        self.execute(resources, sleep_time)

    def execute(self, resources, sleep_time):
        sleep(sleep_time)
        for res in resources:
            with self.res_tab_lock:
                self.resource_table[res][self.id_] = 0
            self.resource_semaphores[res].release()

def fire_node(nodes, num):
    nodes[num].fire()

def print_path(path, vertex):
    if path[vertex] == 0:
        print(vertex, end=' ')
    else:
        print_path(path, path[vertex])
        print("->", vertex, end=' ')

def check_for_deadlock(res_tab, res_tab_lock, num_nodes):
    while True:
        print("[Controller] Starting deadlock detection..")
        adjacency_matrix = [[] for _ in range(num_nodes)]
        with res_tab_lock:
            for row in res_tab:
                to_vertex = [idx for idx in range(num_nodes) if row[idx] == 1][0]
                from_vertices = [idx for idx in range(num_nodes) if row[idx] == -1]
                for v in from_vertices:
                    adjacency_matrix[v].append(to)
        unvisited = list(range(num_nodes))
        cycle = False
        path = []
        last_vertex = -1
        for v in unvisited:
            locally_visited = [v]
            path = [0] * num_nodes
            path[v] = 0
            for vertex in locally_visited:
                unvisited.remove(vertex)
                for u in adjacency_matrix[vertex]:
                    path[u] = vertex
                    if u in locally_visited:
                        last_vertex = u
                        cycle = True
                        break
                    else:
                        locally_visited.append(u)
                if cycle:
                    break
            if cycle:
                break
        if cycle:
            print("[Controller] Deadlock detected! System is UNSAFE!")
            print("[Controller] The cycle is: ")
            print_path(path, last_vertex)
            print()
            # EXIT
        else:
            print("[Controller] No deadlock detected!")

def main():
    m = Manager()
    num_process = 10
    num_resource = 5
    res_tab = [m.list([0] * num_process) for _ in range(num_resource)]
    res_tab = m.list(res_tab)
    res_tab_lock = m.Lock()
    res_sems = m.list([m.Semaphore() for _ in range(num_resource)])
    nodes = [Node(i, res_tab, res_tab_lock, num_resource, res_sems) for i in range(num_process)]

if __name__ == "__main__":
    main()
