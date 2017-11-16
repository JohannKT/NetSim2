import argparse
import random

NET_SPEED = 6 #in mbps
ACK_TIME = 44 #in micro seconds
RTS_CTS_TIME = 30 #in micro seconds
SLOT_TIME = 9 #in micro seconds
DIFS = 28 #in micro seconds
SIFS = 10 #in microseconds
MAX_WAIT = 15 #in slots
INITIAL_CONTENTION_WINDOW = 32
MAX_CONTENTION_WINDOW = 1024

class Packet:
    def __init__(self, id, curr_node, send_node, size, time, algorithm, type='normal', ack_packet = None):
        self.id = id
        self.curr_node = curr_node
        self.send_node =send_node
        self.size = size
        self.time = time
        self.updateTimeSent(self.time)
        self.status = "new"
        self.algorithm = algorithm #dcf or rts
        self.type = type # right now just ACK and normal
        self.slotted_wait = -1 #has not waited yet
        self.ack_packet = ack_packet
        self.backoff_count = 0 #count how many time back off has happend
        self.backoff_wait = 0 #How much the packet should currently wait for backoff
        self.initial_wait = 0
        self.frozen = False #just so we can match the sample log

        if self.type == 'normal':
            self.initial_wait = DIFS
        elif self.type == 'ACK':
            self.initial_wait = SIFS

    def updateTimeSent(self, new_time):
        """
         Used to update the time the packet was actually sent after potentially waiting
        :param new_time:
        :return:
        """
        self.time = new_time
        self.finished_time = self.time + int(self.size/NET_SPEED)
    def dump(self):
        return "Packet {}: {} {} {} {}".format(self.id, self.curr_node, self.send_node, self.size, self.time)
    def addRandomBackoff(self):
        self.backoff_wait = 1024 if self.backoff_count+5 == 10 else 2**(self.backoff_count+5)
        self.backoff_count += 1
        self.updateTimeSent(self.time + self.backoff_wait)

    @staticmethod
    def PacketsFromTrafficFile(traffic, algorithm):
        packets = {}
        count = 0
        for line in traffic:
            elements = line.split()
            p = Packet(int(elements[0]), int(elements[1]), int(elements[2]), int(elements[3]), int(elements[4]), algorithm, "normal")
            packets.setdefault(p.time, []).append(p)
            count += 1
        return packets, count

class WaitList():
    def __init__(self):
        self.list = [] #list of DIFS packets
    def addPacket(self, packet, random_backoff = False):
        packet.slotted_wait = random.randint(0,MAX_WAIT)*SLOT_TIME # has not waited
        if random_backoff:
            packet.addRandomBackoff()
        packet.updateTimeSent(packet.time + packet.initial_wait)
        self.list.append(packet)

    def addPackets(self, packets):
        for p in packets:
            self.addPacket(p)
    def removePacket(self, packet):
        self.list.remove(packet)
    def containsPackets(self):
        return len(self.list)
    def readyDIFS(self, time, ignore = False):
        res = []
        for p in self.list:
            if p.time <= time:
                #DIFS is over check slotted
                p.backoff_wait = 0 # this is to ensure it is zero we we know we have waited the appropriate amount of time
                if p.time == time:
                    if p.frozen:
                        chkPrint("Time: {}: Node {} finished waiting for DIFS and started waiting for {} slots (counter was freezed!)".format(time,p.curr_node,p.slotted_wait / SLOT_TIME),ignore)
                        p.frozen = False
                    else:
                        chkPrint("Time: {}: Node {} finished waiting for DIFS and started waiting for {} slots".format(time, p.curr_node, p.slotted_wait/SLOT_TIME),ignore)
                if p.slotted_wait == 0:
                    res.append(p)
                else:
                    p.slotted_wait -= 1
                    if p.slotted_wait == 0:
                        res.append(p)
        return res

class Channel:
    def __init__(self, algorithm):
        self.dict = {}
        self.count = 0
        self.state = "idle"
        self.algorithm = algorithm
        self.collision = False
    def add(self, packet):
        self.dict.setdefault(packet.finished_time, []).append(packet)
        self.state = "busy"
        self.count += 1
        if self.count > 1:
            self.collision = True
    def remove(self, packet):
        if self.dict.has_key(packet.finished_time):
            if packet in self.dict[packet.finished_time]:
                self.dict[packet.finished_time].remove(packet)
                self.count -= 1
                if self.count == 0:
                    self.state = "idle"
                    self.collision = False
                return True
            else:
                return False
        else:
            #print "Packet not on the wire."
            return False

def chkPrint(msg, ignore=False):
    if not ignore:
        print msg

def dcf(traffic, ignore=False):
    """
      Algorithm: Initially channel is idle, no packets are ready to send
      1) If packets ready to send add packet to waiting list.
      2) If channel idle do 3 else do 4
      3) If wait_list contains packets get packets that are ready and decrement DIFS/Slot counter
      4) increment time
      5) If packet sent put ACK on wait_list
      6) TODO: handle collision
    :param traffic:
    :param ignore:
    :return:
    """
    packets, total_packets = Packet.PacketsFromTrafficFile(traffic, 'dcf')
    chkPrint("Number of lines= {}".format(total_packets), ignore)
    packets_sent = 0
    current_time = 0
    wait_list = WaitList()
    the_channel = Channel('dcf')
    ready_packets = []
    while packets_sent != total_packets:
        ready_packets += packets.get(current_time, [])
        if len(ready_packets) > 0 and the_channel.state != "busy":
            for p in ready_packets:
                wait_list.addPacket(p)
                chkPrint("Time: {}: Node {} started waiting for DIFS".format(current_time, p.curr_node), ignore)
            ready_packets = []

        if the_channel.state == 'idle':
            #SIFS never go on the wait_list
            if wait_list.containsPackets():
                #decrement DIFS wait and send ready packets
                ready_difs = wait_list.readyDIFS(current_time) #this will decrement all SIF packet counters and return ready packets
                for p in ready_difs:
                    p.updateTimeSent(current_time)
                    the_channel.add(p)
                    wait_list.removePacket(p)
                    chkPrint("Time: {}: Node {} finished waiting and is ready to send the packet.".format(current_time,p.curr_node),ignore)
                if the_channel.state == 'busy':
                    for p in wait_list.list:
                        chkPrint("Time: {}: Node {} had to wait for {} more slots that channel became busy!".format(current_time, p.curr_node, p.slotted_wait/SLOT_TIME), ignore)
                        p.frozen = True #so we can match the log output

        elif the_channel.state == 'busy':
            packets_finished = the_channel.dict.get(current_time, [])
            if the_channel.collision:
                for p in packets_finished:
                    the_channel.remove(p)
                    p.updateTimeSent(current_time + p.initial_wait)
                    wait_list.addPacket(p, True) #add random backoff wait time
            else:
                for p in packets_finished:
                    if p.type == 'ACK':
                        chkPrint("Time: {}: Node {} sent {} bits".format(current_time, p.ack_packet.curr_node, p.ack_packet.size),ignore)
                        packets_sent += 1
                        the_channel.remove(p)
                    elif p.type == 'normal':
                        # send ACK
                        ack_packet = Packet(-1, p.send_node, p.curr_node, NET_SPEED*ACK_TIME, current_time, None, "ACK", p)
                        the_channel.remove(p)
                        the_channel.add(ack_packet)

            if the_channel.state == 'idle': #changed from busy to idle
                for p in wait_list.list:
                    p.updateTimeSent(current_time + p.initial_wait + p.backoff_wait) #wait DIFS again
        current_time += 1


def rts(traffic, ignore=False):
    chkPrint("Not implemented", ignore)

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
        dcf(traffic)
    elif sim_type == 'r':
        rts(traffic)
    else:
        print "Simulation type {} is not implemented".format(sim_type)
        print "Type of simulation to run. d - 802.11 DCF Simulation, r - RTS/CTS Simulation"
    pass


if __name__ == "__main__":
    """
        expected arguments: python simulator.py sim_type [gen_file]
    """

    parser = argparse.ArgumentParser(description='Get input for Sim Type and Gnerator file')
    parser.add_argument("sim_type", help="Type of simulation to run. d - 802.11 DCF Simulation, r - RTS/CTS Simulation")
    parser.add_argument("gen_file", nargs='?', help="Filename of file containing generated traffic.", default= "traffic.txt")
    args = parser.parse_args()
    main(args.gen_file, args.sim_type)
