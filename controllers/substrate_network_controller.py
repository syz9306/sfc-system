import sched, time
from threading import Timer
import logging
from algorithms.alg3 import ALG3
from datetime import datetime as dt
import copy

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
# ch = logging.StreamHandler()
ch = logging.FileHandler('./logs/substrate_network_controller.log')
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)
# 'application' code
logger.debug('debug message')
logger.info('info message')
logger.warn('warn message')
logger.error('error message')
logger.critical('critical message')





class SubstrateNetworkController():
    def __init__(self, nw):
        pass
        self.substrate_network = nw
        self.node_info = {}
        self.sfc_list = []
        self.is_stopped = True
        self.update_interval = 1
        self.cpu_threshold = 0.8
        self.over_threshold_nodes_list = []
        self.timer = None
        self.sfc_queue = None
        self.sfc_id_duration = {}
        self.bw_utilization = []
        self.cpu_utilization = []
        self.success_flag = []

        self.counter = 0

        self.alg = None

        self.file_name = './results/' + dt.now().strftime('%Y%m%d%H%M%S') + '.csv'
        with open(self.file_name, "a") as f:
            f.write("No., timestamp, number of sfc, CPU utilization, bandwidth utilization, latency, duration, success, arrival time, depart time" + "\n")


    def start(self):
        if not self.is_stopped:
            self.is_stopped = True
            time.sleep(2*self.update_interval)
        self.is_stopped = False
        self.update()
        self.check_sfc_duration()
        import thread
        thread.start_new_thread(self.run, ())

    def output_nodes_information(self):
        self.substrate_network.print_out_nodes_information()

    def output_edges_information(self):
        self.substrate_network.print_out_edges_information()

    def output_info(self):
        self.output_nodes_information()
        self.output_edges_information()

    def get_nodes_information(self):
        for node in self.substrate_network.nodes():
            self.node_info[node] = self.get_node_information(node)

    def get_node_information(self, node_id):
        cpu_used = self.substrate_network.get_node_cpu_used(node_id)
        cpu_free = self.substrate_network.get_node_cpu_free(node_id)
        cpu_capacity = self.substrate_network.get_node_cpu_capacity(node_id)
        sfc_vnf_list = self.substrate_network.get_node_sfc_vnf_list(node_id)
        total_cpu_used = self.substrate_network.total_cpu_used
        total_cpu_capacity = self.substrate_network.total_cpu_capacity
        return (cpu_used, cpu_free, cpu_capacity, sfc_vnf_list, total_cpu_used, total_cpu_capacity)

    def update(self):

        self.substrate_network.update()
        self.check_cpu_threshold()
        logger.warn(self.over_threshold_nodes_list)
        logger.warn(self.sfc_list)
        # self.check_sfc_duration()
        # if not self.is_stopped:
        #     self.timer = Timer(self.update_interval, self.check_sfc_duration, ()).start()

    def check_node_cpu_threshold(self, node_id):
        cpu_used = self.substrate_network.get_node_cpu_used(node_id)
        cpu_capacity = self.substrate_network.get_node_cpu_capacity(node_id)
        if float(cpu_used)/float(cpu_capacity) > self.cpu_threshold:
            self.over_threshold_nodes_list.append(node_id)
            # print "node:", node_id, "over threshold"
            logger.warn("Node: %s, over threshold", str(node_id))

    def check_cpu_threshold(self):
        self.over_threshold_nodes_list = []
        for node in self.substrate_network.nodes():
            self.check_node_cpu_threshold(node)

    def check_sfc_duration(self):
        time1 = time.time()
        remove_list = []
        for sfc_id, duration in self.sfc_id_duration.items():
            if duration <= 1:
                remove_list.append(sfc_id)
                continue
            self.sfc_id_duration[sfc_id] = duration - 1
        for sfc_id in remove_list:
            self.undeploy_sfc(sfc_id)
        time2 = time.time()
        logger.warn(self.sfc_id_duration)
        if time2 - time1 > 1:
            if not self.is_stopped:
                self.timer = Timer(0, self.check_sfc_duration, ()).start()
        else:
            if not self.is_stopped:
                self.timer = Timer((self.update_interval - (time2 - time1)), self.check_sfc_duration, ()).start()



    def stop(self):
        self.is_stopped = True
        if self.timer:
            self.timer.cancel()

    def deploy_sfc(self, sfc):
        if sfc.id in self.sfc_list:
            print "sfc has been deployed"
            return
        # alg = ALG3()
        alg = self.alg
        alg.clear_all()
        alg.install_substrate_network(self.substrate_network)
        alg.install_SFC(sfc)
        s = time.time()
        alg.start_algorithm()
        s2 = time.time()

        # |-> For test dy algorithm
        # alg2 = ALG3()
        # alg2.clear_all()
        # alg2.install_substrate_network(self.substrate_network)
        # alg2.install_SFC(sfc)
        # alg2.start_algorithm()
        # route_info_2 = alg2.get_route_info()
        # latency_2 = alg2.get_latency()
        # For test dy algorithm END ->|


        route_info = alg.get_route_info()

        number_of_vnf = sfc.number_of_vnfs
        cpu_utilization = 0
        bw_utilization = 0
        is_success = 0
        latency = -1
        current_time = s2
        run_duration = s2 - s

        arrival_time = sfc.arrival_time
        sfc.depart_time = s2

        if route_info:
            self.substrate_network.deploy_sfc(sfc, route_info)
            self.sfc_list.append(sfc.id)
            self.sfc_id_duration[sfc.id] = sfc.duration

            self.deploy_success(sfc)

            # latency = node_info[sfc.get_dst_vnf().get_substrate_node()]['dst']["latency"]
            latency_1 = alg.get_latency()
            is_success = 1

        else:
            self.deploy_failed(sfc)
        # self.substrate_network.update()
        self.update()

        cpu_utilization = self.substrate_network.get_cpu_utilization_rate()
        bw_utilization = self.substrate_network.get_bandwidth_utilization_rate()


        # filename =
        # with open('')
        self.counter += 1
        with open(self.file_name, "a") as f:
            # f.writelines("timestamp, number of sfc, CPU utilization, bandwidth utilization, latency, duration, success")
            line = str(self.counter) + ',' + \
                   str(current_time) + ',' + \
                   str(number_of_vnf) + ',' + \
                   str(cpu_utilization) + ',' + \
                   str(bw_utilization) + ',' + \
                   str(latency) + ',' + \
                   str(run_duration) + ',' + \
                   str(is_success) + ',' + \
                   str(arrival_time) + ',' +\
                   str(s2) + "\n"
            f.write(line)


        print "__________________________________________"
        self.output_info()
        print ""


    def deploy_success(self, sfc):
        print "deploy succeed, sfc: ", sfc.id

    def deploy_failed(self, sfc):
        print "deploy failed, sfc: ", sfc.id

    def get_route_info(self):
        return self.substrate_network.sfc_route_info

    def undeploy_sfc(self, sfc_id):
        if sfc_id not in self.sfc_list:
            print sfc_id, "not on the substrate network"
            return
        # self.stop()
        # time.sleep(self.update_interval*2)
        self.substrate_network.undeploy_sfc(sfc_id)
        self.sfc_list.remove(sfc_id)
        del self.sfc_id_duration[sfc_id]
        self.update()
        # self.start()

    def handle_cpu_over_threshold(self, alg):
        """Seems use to for test. 
        """
        import copy
        ## undeploy the sfc, redeploy sfc by disable the over threshold cpu
        self.stop()
        for node in self.over_threshold_nodes_list:
            # (sfc_id, vnf) = sn.get_node_sfc_vnf_list(node)
            sfc_vnf_list = self.substrate_network.get_node_sfc_vnf_list(node)
            for (sfc_id, vnf) in sfc_vnf_list:
                ## todo: here we should consider which sfc need to be undployed. May according to priority or some history data or SLA. or cost...
                sfc = self.substrate_network.get_sfc_by_id(sfc_id)
                self.undeploy_sfc(sfc_id)
                sn = copy.deepcopy(self.substrate_network)
                sn.set_node_cpu_capacity(node, 0)
                sn.set_node_cpu_free(node, 0)
                alg.install_substrate_network(sn)
                alg.install_SFC(sfc)
                alg.start_algorithm()
                route_info = alg.get_route_info()
                if sfc.id in self.sfc_list:
                    print "sfc has been deployed"
                    return
                self.substrate_network.deploy_sfc(sfc, route_info)
                self.sfc_list.append(sfc.id)
                self.substrate_network.update()
        self.start()
        print ""


    def run(self):
        while not self.is_stopped:
            sfc = self.sfc_queue.peek_sfc()# this is blocking
            print "Substrate network gets a new sfc", sfc.id
            print str(sfc)
            print "queue_size: " + str(self.sfc_queue.qsize())
            s = time.time()
            self.deploy_sfc(sfc)
            self.update()
            s2 = time.time()
            print "algorithm take time: ", s2 - s



    def output_csv(self):
        #  1, cpu_utilization,  bw_utilization, latency, number of sfc,
        pass