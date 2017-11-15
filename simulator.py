import argparse
import pprint

ack_time = 44
slot = 9
difs = 28
sifs = 10
initial_content_size = 32
max_contention = 1024


class Station():
    def __init__(self, id):
        self.id = id
        self.packet_list = {}
        self.idle_time = 0
        self.ready_queue= 0
class Packet:
    def __init__(self, id, curr_node, send_node, size, time, slotted = False):
        self.id = id
        self.curr_node = curr_node
        self.send_node =send_node
        self.size = size
        self.current_backoff = 0
        if not slotted:
            self.slot_size = 0
            self.time = time
        else:
            self.slot_size = self.size
            self.time = time + (self.slot_size - (time % self.slot_size))
        self.finished_time = self.time + self.size - 1  # the time it takes to send 1 bit is 1 microsecond so it takes size microseconds to send the packet
        self.status = "new"
    def updateTimeSent(self, new_time):
        """
         Used in CSMA to update the time the packet was actually sent after potentially waiting
        :param new_time:
        :return:
        """
        self.time = new_time
        self.finished_time = self.time + self.size - 1

    def dump(self):
        return "Packet {}: {} {} {} {}".format(self.id, self.curr_node, self.send_node, self.size, self.time)
class Wire:
    def __init__(self):
        self.dict = {}
        self.count = 0
        self.state = "idle"
    def add(self, packet):
        if self.dict.has_key(packet.finished_time):
            self.dict[packet.finished_time].append(packet)
        else:
            self.dict[packet.finished_time] = [packet]
        self.state = "busy"
        self.count += 1
    def remove(self, packet):
        if self.dict.has_key(packet.finished_time):
            if packet in self.dict[packet.finished_time]:
                self.dict[packet.finished_time].remove(packet)
                self.count -= 1
                if self.count == 0:
                    self.state = "idle"
                return True
            else:
                return False
        else:
            # print "Packet not on the wire."
            return False
    def clearList(self, index):
        self.count -= len(self.dict[index])
        self.dict[index] = []
        if self.count == 0:
            self.state = "idle"

def chkPrint(msg, ignore=False):
    if not ignore:
        print msg

def no_rts(traffic, ignore=False):
    """
    :param traffic: a list of packets as a string (no new line)
    :param ignore: Ignore print statements?
    """
    num_packets = len(traffic)
    ready_dict = {}
    elements = [0, 0, 0, 0, 0]
    """ Since we dont know how many nodes there are - this is a quick way to find
    out by adding them to a set when we read the traffic to make packet objects"""
    node_set = set()
    temp_list = []
    node_list = {}
    num_packets_sent = 0

    for l in traffic:
        elements = l.split()
        p = Packet(int(elements[0]), int(elements[1]), int(elements[2]), int(elements[3]), int(elements[4]))
        temp_list.append(p)
        node_set.add(int(elements[1]))
        if ready_dict.has_key(p.time):
            ready_dict[p.time].append(p)
        else:
            ready_dict[p.time] = [p]

    for node in range(0, len(node_set)):
        node_list[node] = Station(node)


    for packet in temp_list:
        node_list[packet.curr_node].packet_list[packet.time] = packet


    #while num_packets_sent != num_packets:


def main(gen_file, sim_type):
    try:
        with open(gen_file) as f:
            traffic = f.readlines()
        traffic = [x.strip() for x in traffic]
        del traffic[0]
    except Exception as e:
        print "Failed to read traffic file."
        print "Error {}.".format(e.message)
        return
    if sim_type == 'd':
        no_rts(traffic)
    elif sim_type == 'r':
        slotted_aloha(traffic)
    else:
        print "Simulation type {} is not implemented".format(sim_type)
        print "Options are:  'd' - 802.11 DCF, 'r' - 802.11 with RTS/CTS"
    pass



if __name__ == "__main__":
    """
        expected arguments: python simulator.py sim_type [gen_file]
    """

    parser = argparse.ArgumentParser(description='Get input for Sim Type and Gnerator file')
    parser.add_argument("sim_type", help="Type of simulation to run. d - 802.11 DCF r - 802.11 with RTS/CTS")
    parser.add_argument("gen_file", nargs='?', help="Filename of file containing generated traffic.", default= "traffic.txt")
    args = parser.parse_args()
    main(args.gen_file, args.sim_type)
