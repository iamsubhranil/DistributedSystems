from collections import deque
import time
import random

def get_random_bool():
    if random.randint(0, 1) == 1:
        return True
    return False

class Message:

    id_ = 0
    RECORD = 'RECORD'
    DATA = 'DATA'

    def __init__(self, typ, from_, to_):
        self.id = Message.id_
        Message.id_ += 1
        self.type = typ
        self.sender = from_
        self.receiver = to_

    def __repr__(self):
        return "Message(id=%d,type=%s,sender=%d,receiver=%d)" % (self.id, self.type, self.sender.id, self.receiver.id)

class Channel:

    id_ = 0
    # amount of ticks a message will require to
    # move from sender to receiver
    LATENCY = 4

    def __init__(self, from_, to_):
        self.id = Channel.id_
        Channel.id_ += 1
        self.node1 = from_
        self.node2 = to_
        self.messages = deque([None] * Channel.LATENCY)
        from_.channels.append(self)
        to_.channels.append(self)

    def tick(self):
        m = self.messages.popleft()
        while len(self.messages) < Channel.LATENCY:
            self.messages.append(None)
        if m is not None:
            m.receiver.receive(self, m)

    def send(self, node, message_value):
        tosend = self.node1
        if node == self.node1:
            tosend = self.node2
        m = Message(message_value, node, tosend)
        if self not in node.sent_messages:
            node.sent_messages[self] = []
        node.sent_messages[self].append(m)
        self.messages.append(Message(message_value, node, tosend))

    def __repr__(self):
        ret = "Channel(id=%d,between=(%d,%d),messages=%s)" % \
            (self.id, self.node1.id, self.node2.id, [x.type if x is not None else x for x in self.messages])
        return ret

class Node:

    id_ = 0

    def __init__(self):
        self.id = Node.id_
        Node.id_ += 1
        self.channels = []
        # maps a channel to a message []
        self.received_messages = {}
        self.sent_messages = {}

    def receive(self, channel: Channel, message: Message):
        if channel not in self.received_messages:
            self.received_messages[channel] = []
        if message.type == Message.RECORD:
            pass
        self.received_messages[channel].append(message)

    def tick(self):
        # pick a random channel
        channel = random.choice(self.channels)
        # do a send
        if get_random_bool():
            channel.send(self, Message.DATA)
        # tick all the channels
        for i in self.channels:
            i.tick()

    def __repr__(self):
        ret = "Node(id=%d,numchannels=%d)\n" % (self.id, len(self.channels))
        ret += "\tChannels:\n"
        for i in self.channels:
            ret += "\t\t" + repr(i) + "\n"
        ret += "\tSent Messages:\n"
        for i in self.channels:
            if i in self.sent_messages:
                ret += "\t\tChannel: " + str(i.id) + "\n"
                msgs = self.sent_messages[i]
                for j in msgs:
                    ret += "\t\t\t" + repr(j) + "\n"
        ret += "\tReceived Messages:\n"
        for i in self.channels:
            if i in self.received_messages:
                ret += "\t\tChannel: " + str(i.id) + "\n"
                msgs = self.received_messages[i]
                for j in msgs:
                    ret += "\t\t\t" + repr(j) + "\n"
        return ret

class Record:

    def __init__(self):
        pass

def main():
    nodes = []
    num_nodes = 5
    for i in range(num_nodes):
        nodes.append(Node())

    num_channels = 5
    channels = set()
    for i in range(num_channels):
        x, y = random.sample(range(num_nodes), 2)
        if (x, y) not in channels:
            c = Channel(nodes[x], nodes[y])
            channels.add((x, y))
    # make sure that all nodes have at least one channel
    for j, i in enumerate(nodes):
        if len(i.channels) == 0:
            c = j
            while c == j:
                c = random.choice(range(num_channels))
            c = Channel(nodes[j], nodes[c])
    print(nodes)

    while True:
        for node in nodes:
            node.tick()
        time.sleep(2)
        print(nodes)

if __name__ == "__main__":
    main()
