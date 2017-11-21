import argparse
import random
import numpy as np
from scipy.stats import truncnorm
import time
import os
import sys



""" calculate gap using the following formula:
          pkt_size             offered_load
        --------------    =   ---------------
        pkt_size + gap           num_node
"""


max_packet_size = 2000
min_packet_size = 100


def getKey(item):
    return item[0]

def get_truncated_normal(mean=0, low=1):
    upp = 2*mean
    sd = mean / 6
    return truncnorm((low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)

def calculate_gap(pkt_size, num_node, offered_load):
    #TODO right now we force it to be an int but we need to figure out if it is the floor or ceiling we should be using
    return int((((pkt_size * num_node) / offered_load) - pkt_size))

def choose_node(num_node):
    return random.randint(0,num_node-1)

def get_send_node(num_node, cur_node):
    send = random.randint(0,num_node-1)
    while send == cur_node:
        send = random.randint(0,num_node-1)
    return send


def generate_file(num_node, offered_load, num_pkts_per_node, dist, seed=None, gen_file = True ):
    # create dict for keeping track of packets sent by each node
    # Each dict's key is the node number
    pkt_size = random.randint(min_packet_size, max_packet_size)

    packets_sent = {}
    node_time = {}
    packets_left = num_pkts_per_node * num_node #total number of packets
    current_time = 0
    output_array= []
    pkt_sizes = []
    count = 0 #used for creating unique packet IDs
    for x in range(0, packets_left):
        pkt_sizes.append(random.randint(100,2000))
    avg_size = int(sum(pkt_sizes) / float(len(pkt_sizes)))
    if(dist == 'n'):
        norm = get_truncated_normal(avg_size)
        norm = norm.rvs(packets_left)
        avg_size = int(sum(norm) / float(len(norm)))
    elif dist == 'u':
        gap = int(calculate_gap(avg_size, num_node, offered_load))
    else:
        print "invalid Distribution type 'u' - uniform, 'n' - normal"
        sys.exit(1)



    if gen_file:
        outfile = open("traffic.txt", "w")
        outfile.write(str(packets_left) + "\n") #per project guidlines, the first line of output should be the total number of packets in the file
    #initialize to amount they will each send
    for x in range(0, num_node):
        packets_sent[x] = num_pkts_per_node
        node_time[x] = 0

    #keep going until all values in dict are 0 meaning all have sent their packets
    while  not all(value == 0 for value in packets_sent.values()):
        if(dist == 'u'):
            rand_gap = random.randint(0,2*gap)
            pkt_size =  pkt_sizes.pop()
        elif(dist == 'n'):
            rand_gap = int(random.choice(norm))
            pkt_size =  pkt_sizes.pop()


        cur_node = 0

        while True:
            cur_node = choose_node(num_node)
            if packets_sent[cur_node] == 0:
                if all(value == 0 for value in packets_sent.values()):
                    break
                else:
                    cur_node = choose_node(num_node)
            else:
                break

        send_node = get_send_node(num_node, cur_node)
        pkt_id = count
        node_time[cur_node] = node_time[cur_node] + rand_gap
        current_time = node_time[cur_node]


        packets_sent[cur_node] = packets_sent[cur_node] - 1
        output_array.append(  (current_time, str(pkt_id) + " " + str(cur_node) + " " + str(send_node) + " "+ str(pkt_size) + " "+ str(current_time) +"\n") )
        count = count + 1
    #sort by time
    output_array = sorted(output_array, key= getKey)
    if gen_file:
        for x in output_array:
            outfile.write(x[1])
    return [x[1] for x in output_array]


if __name__ == "__main__":
    """handling arguments to the program
    expected use is the following:
    python generator.py num_node pkt_size offered_load num_pkts_per_node'[seed]
    """
    parser = argparse.ArgumentParser(description='Get input to generator')
    parser.add_argument("num_node", help="The number of nodes used in simulation.", type=int)
    parser.add_argument("offered_load", help=" measure of the traffic compared to the channel capacity.", type=float)
    parser.add_argument("num_pkts_per_node", help=" Number of packets sent per node in traffic file generated.", type=int)
    parser.add_argument("dist", help="Uniform or Exponential Distribution.", type=str)
    parser.add_argument('seed', nargs='?', default=time.time(), type=int)



    args = parser.parse_args()
    #this is just so it easier to call generate_file from a script (so we can auto generate traffic)
    generate_file(args.num_node, args.offered_load, args.num_pkts_per_node, args.dist, args.seed)
