import uuid
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import time,pickle as pk
import json


'''
Transaction and Block details
'''
class Transaction(object):
    def __init__(self, data, hash, meta = None) -> None:
        data = pk.loads(data)
        self.timestamp = data['timestamp']
        self.inputs = data['inputs']
        self.output = data['output']
        self.hashcode = pk.loads(hash)
        self.sender = data['sender']
        self.message = pk.dumps(data)
        self.meta = meta
        self.trans_id = data['id']
    
    def verify_local(self):
         assert all([v > 0 for _,v in self.inputs]), "not >0"
         assert sum([float(v) for _,v in self.inputs]) == float(self.output), "wrong"
         serialization.load_ssh_public_key(self.sender).verify(self.hashcode, self.message, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.MAX_LENGTH),hashes.SHA256())
    

    def create_transaction_meta(priv_key, pub_key, inputs : list, output : float, id : str = None):
        id =  id if id else uuid.uuid4().hex
        data = pk.dumps({'timestamp' : int(time.time() * 1000), 'inputs' : inputs, 
        'output' : output, 'sender' : pub_key, 'id' : id})
        hash = pk.dumps(priv_key.sign(data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.MAX_LENGTH),hashes.SHA256()))
        return [{'data' : data, 'hash' : hash, 'id' : id}]
    
    def __str__(self) -> str:
        inputs = [[str(u)[:20] + '...', str(v)] for (u,v) in self.inputs]
        meta_input = map(lambda x: x[0] + ['key_index ' + x[1]] , zip(inputs, self.meta['inputs']))
        output = {
            'sender' : str(self.sender)[:20] + '...' if not self.meta else str(self.sender)[:20] + '... key_index ' + self.meta['sender'], 
            'inputs' : inputs if not self.meta else list(meta_input),
            'output' : self.output,
            'hash' : self.hashcode.hex()[:20] + '...',
            'id' : self.trans_id
        }
        return json.dumps(output)



class Block(object):
    def __init__(self, tr:list[str], prev_hash = None, idx = 0, nonce = 0, tr_meta = None) -> None:
        self.transactions = [Transaction(e['data'] , e['hash'], f)  for e, f in zip(pk.loads(tr), tr_meta)]
        self.timestamp = time.time()
        self.idx = idx
        self.nonce = nonce
        self.prev_hash = prev_hash
    
    def verify_local(self):
        for e in self.transactions: e.verify_local()

    def not_present_already(self, id):
        for e in self.transactions: 
            if e.trans_id == id: return False
        return True
    
    def get_tr_hash(self):
        return set([e.hashcode for e in self.transactions])
    
    def has_proper_tr(self, old_tr = set()):
        now = self.get_tr_hash()
        join =  now | old_tr
        assert join == now, f"Blocks transaction set not same Error : {len(old_tr)} {len(now)}" #replca with merkle root
    
    def get_senders(self, hashes):
        A = []
        for hash in hashes:
            for e in self.transactions: 
                if e.hashcode == hash: A.append(e.sender)
        return A
    
    def update_prev_block_copy(self, hash, tr:list[str],  tr_meta = None):
        self.prev_hash = hash
        self.transactions.extend([Transaction(e['data'] , e['hash'], f)  for e, f in zip(tr, tr_meta)])
        self.timestamp = time.time()
        self.idx += 1


    def get_hash(self):
        digest = hashes.Hash(hashes.SHA256())
        digest.update(pk.dumps(self.__dict__))
        return digest.finalize()

    def check_balance(self, pk):
        s = 0
        for tr in self.transactions:
            for r,amt in tr.inputs:
                if r == pk: s+=amt
                if tr.sender == pk: s-=amt
        return s
    
    def __str__(self) -> str:
        output = {
            'transactions' : [str(t) for t in self.transactions],
            'prev_hash' : self.prev_hash.hex()[:20] + '...' if self.prev_hash else None,
            'nonce' : self.nonce,
            'block_number' : self.idx
        }
        return json.dumps(output)