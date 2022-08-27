import pickle as pk
import os, tqdm
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives._serialization import Encoding,PublicFormat,BestAvailableEncryption,PrivateFormat

password = b'ABCD' #dummy password

'''
generate private & public keys
'''
def generate_keys(num_keys = 5):
    if not os.path.exists('keys'): os.mkdir('keys')
    for _ in tqdm.tqdm(range(num_keys)): 
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        prk = private_key.private_bytes(encoding=Encoding.PEM, format=PrivateFormat.OpenSSH, encryption_algorithm=BestAvailableEncryption(password))
        pubk = private_key.public_key().public_bytes(encoding=Encoding.OpenSSH, format=PublicFormat.OpenSSH)
        key_idx = int.from_bytes(os.urandom(1), byteorder="big")
        with open(f'keys/{key_idx}.pk' , 'wb') as f: 
            pk.dump({'public' : pubk, 'private' : prk}, f)

'''
Simple network High level class which we will use to communicate with other nodes 
'''
class AbstractNetwork(object):
    def send_messages(self): pass


'''
Client for Toy Coin, to interact with the network
'''
class ToyClient(object):
    
    def __init__(self ,network : AbstractNetwork , node_addr = None, is_miner = True) -> None:
        self.is_miner = is_miner
        self.exit = False
        self.network = network
        assert node_addr is not None
        self.addr = node_addr
        self.chain = []
        self.messages = []

    def register_from_json(self, key_idx):
        '''
        register a key-pair with the client with the key_idx from keys/{key_idx}.pk file, called for each operation
        '''
        pass
    

    def mine_network(self):
        '''
        starts adding transactions to the network
        '''
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
    
    def view_balance(self):
        '''
        Find the balance of each client
        '''
        pass
    
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
    

    def add_to_messages(self, msg):
        ''' messages recieved from the network '''
        self.messages.append(msg)