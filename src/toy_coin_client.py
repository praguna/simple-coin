from distutils.command.build import build
from enum import Enum
import pickle as pk
import os, tqdm, copy
from queue import Queue
import random as r
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives._serialization import Encoding,PublicFormat,BestAvailableEncryption,PrivateFormat
from transaction_and_block import *

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
get key objects from pickle files
'''
def extract_keys(file_name):
    with open(os.path.join('keys', file_name), 'rb') as f: 
        key_pair = pk.load(f)
        key_pair['public'] = key_pair['public']
        key_pair['private'] = serialization.load_ssh_private_key(key_pair['private'], password)
    return key_pair


'''
Add the zero block
'''
def zero_block():
    if not os.path.exists('keys'): raise Exception("keys not found")
    all_keys = os.listdir('keys')
    zero_user_file = r.choice(all_keys)
    zero_key = extract_keys(zero_user_file)
    inputs = [(extract_keys(e)['public'], 10000) for e in all_keys]
    meta_info = [{'sender' : zero_user_file, 'inputs' : all_keys}]
    tr = pk.dumps(Transaction.create_transaction_meta(zero_key['private'], zero_key['public'], inputs, len(all_keys) * 10000))
    print('created zero block')
    return Block(tr = tr, tr_meta=meta_info)
    

'''
Simple network High level class which we will use to communicate with other nodes 
'''
class AbstractNetwork(object):
    def send_messages(self, toyClient, message, call_back): pass



class MessageType(Enum):
    Tr = "Transaction"
    Bl = "Block"


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
        self.chain : list[Block] = []
        self.tr_list = Queue()
        self.block_list = Queue()
        self.keys = None
        self.miner_key_idx = None

    def register(self, key_idx):
        '''
        register a key-pair with the client with the key_idx from keys/{key_idx}.pk file, called for each operation
        '''
        self.key_idx = key_idx
        self.keys = extract_keys(key_idx + '.pk')
        return self
    
    def register_as_miner(self, key_idx):
        '''
        This key-pair will recieve all transaction fees for mining
        '''
        self.miner_key_idx = key_idx
        self.miner_keys = extract_keys(key_idx + '.pk')
    

    def mine_network(self):
        '''
        starts adding transactions to the network
        '''
        ts_data, ts_meta = self.fetch_transactions() #get all transaction objects of same timestamp
        if len(ts_data) == 0: return
        # self.sync_chain() #make sure largest chain is present
        is_valid, block = self.validate_transactions(ts_data, ts_meta) 
        if not is_valid: return False
        block = self.find_nonce(block) # proof of work
        msg = {'type' : MessageType.Bl, 'block' : block} #send to all nodes
        self.network.send_messages(self, msg)
        print('Broacasting transaction from node ', self.addr)
        self.sync_chain(block) # try to add this block


    def build_msg(self, transaction : list[(int, float)]):
        '''
        send transaction to a miner, using a closure for network to fill after communication
        '''
        transaction = [(a + '.pk', b) for a,b in transaction]
        def get_msg(miner_key_idx):
            new_transaction = transaction + [(miner_key_idx + '.pk', 1)] #fee
            inputs = [(extract_keys(a)['public'] , b) for a,b in new_transaction] # for Transaction object
            new_transaction = [a for a,_ in new_transaction] # for meta which requires only file name
            s = sum([b for _,b in inputs])
            tr = Transaction.create_transaction_meta(self.keys['private'], self.keys['public'], inputs, s)
            msg = {'type' : MessageType.Tr,  'tr' : tr , 'meta' :[{'sender' : self.key_idx + '.pk', 'inputs' : new_transaction, 'pub_key' : self.keys['public']}]}
            return msg , tr[0]['hash']
        return get_msg



    def send_and_verifiy_transaction(self, transaction : list[(int, float)]):
        '''
        submit transaction for verification
        '''
        print('sending the transaction ...')
        # without adding transaction fee
        # transaction = [(a + '.pk', b) for a,b in transaction]
        # inputs = [(extract_keys(a)['public'] , b) for a,b in transaction] # for Transaction object
        # transaction = [a for a,_ in transaction] # for meta which requires only file name
        # s = sum([b for _,b in inputs])
        # tr = Transaction.create_transaction_meta(self.keys['private'], self.keys['public'], inputs, s)
        # msg = {'type' : MessageType.Tr,  'tr' : tr , 'meta' :[{'sender' : self.key_idx + '.pk', 'inputs' : transaction, 'pub_key' : self.keys['public']}]}
        # self.network.send_messages(self, msg)
        # encoded_hashes = [tr[0]['hash']] 
        msg_func = self.build_msg(transaction)
        encoded_hashes = self.network.send_messages(self, msg_func, call_back=True)
        is_verified = False
        s, e = time.time(), time.time()
        print('waiting for verification ... (max 10 secs) timeout')
        hash = [pk.loads(e) for e in encoded_hashes]
        while not is_verified and (e - s <= 10):
            is_verified = self.verify_transaction(hash)
            e = time.time()
        if not is_verified: print("Was not able to verify the transaction!, retry verification with the hash")
        return is_verified
    
    def view_balance(self):
        '''
        Find the balance of each client, asssumes no stubbing
        '''
        e = self.chain[-1]
        return e.check_balance(self.keys['public'])
    
    def verify_transaction(self, hashes):
        '''
        find the block using timestamp and the branch of the transaction, assumes no stubbing so the last block
        '''
        e = self.chain[-1]
        return any([not e.not_present_already(hash) for hash in hashes])
    
    def find_nonce(self, block : Block):
        '''
        find a unique hash with first 8 digits being zero
        '''
        # logic to find the right nonce
        block.nonce+=1
        print('starting nonce puzzle at : ', self.addr)
        s = f'{int(block.get_hash().hex(),16) :0>40b}'[1:9]
        while s != '0'*8: 
            s = f'{int(block.get_hash().hex(),16) :0>40b}'[1:9]
            block.nonce+=1
        print('done with puzzle :', self.addr, time.time(), block.nonce)
        return block
    
    def fetch_transactions(self):
        '''
        check for any transaction is present in the messages
        '''
        ts_data, ts_meta = [], []
        while len(ts_data) == 0 and self.is_miner:
            limit = 10
            while limit > 0 and not self.tr_list.empty():
                tr, meta = self.tr_list.get()
                ts_data.extend(tr)
                ts_meta.extend(meta)
                limit-=1
        return ts_data, ts_meta
        

    def sync_chain(self, block : Block):
        '''
        new blocks in message list
        '''
        prev_block : Block = self.chain[-1]
        is_solved = any([b.prev_hash == block.prev_hash for b in self.chain])
        if is_solved: 
            print("Not adding as the block for this address already exists, node : ",self.addr)
            return
        try:
            block.verify_local()
            hashes = block.get_tr_hash() - prev_block.get_tr_hash()
            val = all([prev_block.not_present_already(e) for e in hashes]) # allow new hashes only
            if not val: raise Exception('Invalid Block : Invalid transaction')
            sender_pk = block.get_senders(hashes)
            val = all([block.check_balance(pk) >= 0 for pk in sender_pk])
            if not val: raise Exception('Invalid Block : Invalid balance')

        except Exception as e:
            print('Invalid transactions in the block found at node ',self.addr,' hence not adding to chain')
            print(e)
            return

        print('Added Block at node : ', self.addr)
        self.chain.append(block)

    def validate_transactions(self, ts_data, ts_meta):
        '''
        prevent doubled spending using chain transactions
        '''
        sender_pk = [e['pub_key'] for e in ts_meta]
        prev_block = self.chain[-1]
        new_block = copy.deepcopy(prev_block)
        val = all([new_block.not_present_already(e['hash']) for e in ts_data]) # allow new hashes only
        if not val: return val, None
        new_block.update_prev_block_copy(prev_block.get_hash(), ts_data, ts_meta)
        try:
            new_block.verify_local() # check >0 amount and properly signed 
        except Exception as e: 
            print('Verification Failure at node : ',self.addr, e)
            return False, None
        val = all([new_block.check_balance(pk) >= 0 for pk in sender_pk]) # no double spending
        if not val : print("Double spending Error : ", self.addr)
        return val, new_block
    

    def add_to_messages(self, msg):
        ''' messages recieved from the network '''
        if msg['type'] == MessageType.Bl:
            block = msg['block']
            print('volia, recieved broadcast block from node at ',self.addr)
            self.sync_chain(block)
            
        if msg['type'] == MessageType.Tr:
            meta_info = msg['meta']
            tr = msg['tr']
            print('voila, recieved transaction from node : ',meta_info[0]['sender'])
            self.tr_list.put((tr, meta_info))
    
    def print_chain(self):
        '''
        print chain on terminal
        '''
        print()
        for e in self.chain: 
            print(e, end = '')
            print('=>\n\n' if e.get_hash()!=self.chain[-1].get_hash() else '')
        print()