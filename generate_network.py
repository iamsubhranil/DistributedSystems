import sys

def main():
    if len(sys.argv) == 3:
        num_nodes = int(sys.argv[1])
        fname = sys.argv[2]
    else:
        num_nodes = int(input("Enter number of nodes in the network: "))
        fname = input("Enter file name to save: ")

    with open(fname, "w") as f:
        f.write(str(num_nodes))
        print("digraph G {")
        print("graph [overlap = scale];")
        import random
        for i in range(num_nodes):
            f.write("\n")
            num_neighbours = random.randint(1, num_nodes)
            neighbours = []
            while len(neighbours) == 0:
                neighbours = random.sample(range(1, num_nodes + 1), num_neighbours)
                if neighbours.count(i + 1) > 0:
                    neighbours.remove(i + 1)
            first = str(neighbours[0])
            rest = "".join(map(lambda x: " " + str(x), neighbours[1:]))
            print(i + 1, "-> {", first + rest, "};")
            f.write(first + rest)
        print("}")

if __name__ == "__main__":
    main()
