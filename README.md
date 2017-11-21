# NetSim2
#### Authors: Johann Thairu and Shawn Stone
#### CNT5505 Data Communications Assignment 3
## To Run (Make sure you are using python 2.7)

#### Generate Traffic (Traffic will be generated in 'traffic.txt')
```
python generator.py -h
python generator.py <num_node> <offered_load> <num_pkts_per_node> [seed]
```
#### Simulate Traffic (Simulation will print to stdout)
```
python simulator.py -h
python simulator.py <sim_type> [gen_file]
```
The default gen_file is 'traffic.txt'
