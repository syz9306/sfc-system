import time
import random
import copy
import sys
from topology.nsfnet import NSFNET
from topology.jpn48_network import JPN48
import matplotlib.pyplot as plt

from sfc_examples import sfc1
from controllers.sfc_generator import SFCGenerator

from algorithms.alg3 import ALG3
from algorithms.random_algorithm import RandomAlgorithm
from algorithms.greedy_algorithm import GreedyAlgorithm
from algorithms.dynamic_programming_algorithm import DynamicProgrammingAlgorithm
from algorithms.k_shortest_paths_algorithm import KShortestPathsAlgorithm
from algorithms.betweenness_centrality_algorithm import BetweennessCentralityAlgorithm
DPAlgorithm = DynamicProgrammingAlgorithm()
GDAlgorithm = GreedyAlgorithm()
KPathsAlgorithm_1 = KShortestPathsAlgorithm(1)
KPathsAlgorithm_10 = KShortestPathsAlgorithm(10)
BCAlgorithm = BetweennessCentralityAlgorithm()
RAAlgorithm = RandomAlgorithm()

substrate_network = JPN48
substrate_network_dp = copy.deepcopy(substrate_network)
substrate_network_gd = copy.deepcopy(substrate_network)
substrate_network_k1 = copy.deepcopy(substrate_network)
substrate_network_k10 = copy.deepcopy(substrate_network)
substrate_network_bc = copy.deepcopy(substrate_network)
substrate_network_ra = copy.deepcopy(substrate_network)


sfc_dict = {
    "name": "sfc_1",
    "type": "xx",
    "vnf_list": [
        {"type": 2, "name": "vnf1", "CPU": 10},
        {"type": 2, "name": "vnf2", "CPU": 20},
        {"type": 2, "name": "vnf3", "CPU": 30},
        # {"type": 2, "name": "vnf4", "CPU": 40},
        # {"type": 2, "name": "vnf5", "CPU": 40},
        # {"type": 2, "name": "vnf6", "CPU": 40},

    ],
    "bandwidth": 10,
    # "src_node": random.randint(0, 13),
    # "dst_node": random.randint(0, 13),
    "src_node": 0,
    "dst_node": 0,
    "latency": 10,
    "duration": 20
}



dp_latency_list = []
gd_latency_list = []
ks1_latency_list = []
ks10_latency_list = []
bc_latency_list = []
ra_latency_list = []




def deploy_sfc(deployment_algorithm, substrate_network, sfc, update=False):
    print "---------- " + deployment_algorithm.name + " ----------------------------"
    deployment_algorithm.clear_all()
    deployment_algorithm.install_substrate_network(substrate_network)
    deployment_algorithm.install_SFC(sfc)
    start_time = time.time()
    deployment_algorithm.start_algorithm()
    end_time = time.time()
    route_info = deployment_algorithm.get_route_info()
    latency = deployment_algorithm.get_latency()
    if update:
        substrate_network.deploy_sfc(sfc, route_info)
        substrate_network.update()
    substrate_network.print_out_edges_information()
    substrate_network.print_out_nodes_information()
    return (route_info, latency, (end_time - start_time))


# (dp_route_info, dp_latency, dp_execution_time) = deploy_sfc(DPAlgorithm, substrate_network, sfc)
count = 0
fail_count = 0
for src in range(0, 1):
    for dst in range(0, 20):
        count += 1
        if src == dst:
            continue
        print 'src -> dst:', src, dst
        sfc_dict['src_node'] = src
        sfc_dict['dst_node'] = dst
        sfc = SFCGenerator(sfc_dict).generate()

        (dp_route_info, dp_latency, dp_execution_time) = deploy_sfc(DPAlgorithm, substrate_network_dp, sfc, update=True)
        (gd_route_info, gd_latency, gd_execution_time) = deploy_sfc(GDAlgorithm, substrate_network_gd, sfc, update=True)
        (ks1_route_info, ks1_latency, ks1_execution_time) = deploy_sfc(KPathsAlgorithm_1, substrate_network_k1,
                                                                       sfc, update=True)
        (ks10_route_info, ks10_latency, ks10_execution_time) = deploy_sfc(KPathsAlgorithm_10, substrate_network_k10,
                                                                          sfc, update=True)
        (bc_route_info, bc_latency, bc_execution_time) = deploy_sfc(BCAlgorithm, substrate_network_bc,
                                                                    sfc, update=True)
        # t = 0
        # sum_latency = []
        # for i in range(0, 100):
        #     (ra_route_info, ra_latency, ra_execution_time) = deploy_sfc(RAAlgorithm, substrate_network, sfc)
        #     if ra_latency != None:
        #         sum_latency.append(ra_latency)
        # ra_latency = sum(sum_latency) * 1.0 / len(sum_latency)
        (ra_route_info, ra_latency, ra_execution_time) = deploy_sfc(RAAlgorithm, substrate_network_ra, sfc, update=True)
        # (al3_route_info, al3_latency, al3_execution_time) = deploy_sfc(ALG, substrate_network, sfc)
        # print 'dp, gd, ks1, ks10, bc, ra, al3'
        print dp_latency, gd_latency, ks1_latency, ks10_latency, bc_latency, ra_latency
        dp_latency_list.append(dp_latency)
        gd_latency_list.append(gd_latency)
        ks1_latency_list.append(ks1_latency)
        ks10_latency_list.append(ks10_latency)
        bc_latency_list.append(bc_latency)
        ra_latency_list.append(ra_latency)
        if (gd_latency < dp_latency or ks1_latency < dp_latency or ks10_latency < dp_latency) and gd_latency != None and ks1_latency != None and ks10_latency != None:
            fail_count += 1
            raw_input("press any key to continue")

print count
print fail_count
plt.plot(dp_latency_list)
plt.plot(gd_latency_list)
plt.plot(ks1_latency_list)
plt.plot(ks10_latency_list)
plt.plot(bc_latency_list)
plt.plot(ra_latency_list)
plt.show()
sys.exit(0)
