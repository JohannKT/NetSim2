import generator
import simulator
import time
import numpy as np
import matplotlib.pyplot as plt
import datetime
from multiprocessing.pool import ThreadPool


def getTraffic(num_node, offered_load, num_pkts_per_node, dist, average_packet, seed = time.time()):
    """
    Generates traffic based on the parameters and returns it in a way that it can be passed to the simlator functions
    :return:
    """
    generate_file = False #for readability
    traffic = generator.generate_file(num_node, offered_load, num_pkts_per_node, dist, average_packet, seed)
    del traffic[0]
    traffic = [x.strip() for x in traffic]
    return traffic



def dcfAnalysis(traffic):
    """

    :param traffic: should be the return value of getTraffic
    :return: returns a tuple (successfully_transmitted, failed, throughput)
    """
    return simulator.dcf(traffic, True)

def rAnalysis(traffic):
    """

    :param traffic: should be the return value of getTraffic
    :return: returns a tuple (successfully_transmitted, failed, throughput)
    """
    return simulator.rts(traffic, True)

def generateGraph(vals):
    """
      Plot the graph similar to Figure 4-4 on page 268 of the text book
    :param vals: Dictionary containing Aloha:[(utilization,offered_load),..], Slotted:[(utilization,offered_load),..], CSMA:[(utilization,offered_load),..]
    :return: None
    """
    #TODO convert throughput to utilization
    for key,v in vals.items():
        if key == "RTS/CTS":
            type = 'b-' #blue
        elif key == "Dcf":
            type = 'g-' #green
        else:
            type = 'y-' #shouldn't be possible
        x_vals = [y[1] for y in v]
        y_vals = [y[0] for y in v]
        plt.plot(x_vals, y_vals, type, label=key)

    plt.xlabel("Offered Load")
    plt.xticks(np.arange(0, 8.5 + 0.5, 0.5))
    plt.ylabel("S (throughput per packet time)")
    plt.legend(loc='best')
    plt.savefig("{}_range_{}_{}.png".format(str(datetime.datetime.today()).replace(' ', '_').replace(':','_'), 0.5, 8.5))
    plt.show() # should probably create png or something

def main():
    throughput_to_offeredLoad = {"Dcf":[], "RTS/CTS":[]}
    offered_loads = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0]
    num_node = 5
    dist = 'u'
    average_packet = 300
    num_pkts_per_node = 10000 # total of 100,000 packets per requirements
    max_utilization = 1000.0 #1000 kbps = 1mbps, we are at max if we are using the entire 1mbps
    pool = ThreadPool(processes=2)

    for ol in offered_loads:
        print "Trying load: {}".format(ol)
        traffic = getTraffic(num_node, ol, num_pkts_per_node, dist, average_packet )
        #returns (throughput, the_channel.total_transmitted, the_channel.collision_count, free_percentage, station_stats)
        dcf = pool.apply_async(rAnalysis, ([traffic]))
        rts = pool.apply_async(dcfAnalysis, ([traffic]))
        throughput_to_offeredLoad["Dcf"].append((dcf.get()[2] / max_utilization, ol))
        throughput_to_offeredLoad["RTS/CTS"].append((rts.get()[2] / max_utilization, ol))
        if ol > 4:
            break


    generateGraph(throughput_to_offeredLoad)

if __name__ == "__main__":
    main()
