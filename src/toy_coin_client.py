'''
Client for Toy Coin, to interact with the network
'''
class ToyClient(object):
    
    def __init__(self ,is_miner = True) -> None:
        self.is_miner = is_miner
        self.addr = None
        self.chain = []
        self.nodes = []
        self.requests = []
        self.my_addr = []

    def register(self, pharse = None):
        '''
        create keys with the pharse
        '''
        assert pharse is not None
        self.pharse = pharse
        return self.generate_keys(pharse)
    

    def mine_network(self):
        '''
        starts adding transactions to the network
        '''
        self.broad_cast(self.addr)
        ts = self.fetch_transactions() #get all transaction objects of same timestamp
        self.sync_chain() #make sure largest chain is present
        is_valid = self.validate_transactions(ts) 
        if not is_valid: return (False, ts)
        block = self.find_nonce(ts) # proof of work
        votes = self.broad_cast(block) #send to all nodes
        if votes >= 0.51: self.add_block(block)
        else: self.sync_chain() #make sure largest chain is present
        
    def send_and_verifiy_transaction(self, transaction):
        '''
        submit transaction for verification
        '''
        self.broad_cast(transaction)
        is_verified = False
        while not is_verified:
            self.sync_chain() #make sure largest chain is present
            is_verified = self.verify_transaction(transaction)
        return is_verified
    
    def verify_transaction(self, transaction):
        '''
        find the block using timestamp and the branch of the transaction
        '''
        pass
    
    def find_nonce(self, ts):
        '''
        find a unique hash with first 8 digits being zero
        '''
        nonce = self.chain[-1]['nonce']
        block = self.package_block(ts, nonce) 
        # logic to find the right nonce
        return block
    
    def fetch_transactions(self):
        '''
        check for any transaction is present in the messages
        '''
        pass

    def sync_chain(self):
        '''
        new blocks in message list and ask all blocks from neighbours
        '''
        pass

    def validate_transactions(self, ts):
        '''
        prevent doubled spending using chain transactions
        '''
        pass

    def package_block(self, ts, nonce):
        '''
        package with timestamp+ts+nonce in a json
        '''
        pass

    def broad_cast(self, message):
        '''
        send the message to all nodes
        '''
        pass

    def add_block(self, block):
        '''
        update the chain locally
        '''
        pass
    
    def generate_keys(self):
        '''
        generate private & public keys
        '''
        pass