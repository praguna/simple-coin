import threading
from toy_coin_client import ToyClient, AbstractNetwork
from queue import Queue
'''
Decentralized network, attaching each node (simulated by 2 threads -- for mining & recieving messages) for each client
'''

class Network(AbstractNetwork):

    def __init__(self, num = 5) -> None:
        '''create a network with 5 nodes'''
        super(AbstractNetwork, self).__init__()
        self.nodes : dict = {}
        self.clients = []
        self.num = num
        for idx in range(num): 
            self.clients.append(ToyClient(self, idx, True))
            self.nodes[idx] = Queue()

    def get_clients(self):
        assert self.clients[0].addr != None
        return self.clients

    def start(self):
        self.mine_threads = [threading.Thread(target=self.mine_local_network, args=[k]) for k in self.clients]
        self.message_threads = [threading.Thread(target=self.listen_to_messages, args=[k]) for k in self.clients]
        for t1, t2 in zip(self.mine_threads, self.message_threads):  t1.start() , t2.start()
    
    def stop(self):
        for k in self.clients: 
            k.is_miner, k.exit = False, True
        for t1, t2 in zip(self.mine_threads, self.message_threads):  t1.join(), t2.join()

    def mine_local_network(self, toyClient : ToyClient):
        print('Starting miner at node :',toyClient.addr)
        while toyClient.is_miner:
            # try:
                toyClient.mine_network()
            # except Exception as e: print(e)
        print('Closing miner at node :',toyClient.addr)
        
    def listen_to_messages(self, toyClient : ToyClient):
        print('Starting message queue at node:',toyClient.addr)
        while not toyClient.exit:
            q  : Queue = self.nodes[toyClient.addr]
            while not q.empty():
                # try:
                    msg = q.get()
                    toyClient.add_to_messages(msg)
                # except Exception as e: print(e)
        print('Closing message queue at node:',toyClient.addr)
                  
    def send_messages(self, toyClient : ToyClient, message, call_back = None):
        objs = [] # only for call back
        for k,v in self.nodes.items():
            if self.clients[k].addr != toyClient.addr: 
                if call_back: 
                    msg, tr_hash = message(self.clients[k].miner_key_idx)
                    v.put(msg), objs.append(tr_hash)
                else: v.put(message)
        return objs