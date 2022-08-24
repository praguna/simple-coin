from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import time,pickle as pk


'''
Transaction and Block details
'''
class Transaction(object):
    def __init__(self, data, hash) -> None:
        data = pk.loads(data)
        self.timestamp = data['timestamp']
        self.inputs = data['inputs']
        self.output = data['output']
        self.hashcode = pk.loads(hash)
        self.sender = data['sender']
        self.message = pk.dumps(data)
    
    def verify_local(self):
         assert sum([float(v) for _,v in self.inputs]) == float(self.output)  
         serialization.load_ssh_public_key(self.sender).verify(self.hashcode, self.message, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.MAX_LENGTH),hashes.SHA256())



class Block(object):
    def __init__(self, tr:list[str], prev_hash = None) -> None:
        self.transactions = [Transaction(e['data'] , e['hash'])  for e in pk.loads(tr)]
        self.timestamp = time.time()
        self.prev_hash = prev_hash
    
    def verify_local(self):
        for e in self.transactions: e.verify_local()

    def get_hash(self):
        digest = hashes.Hash(hashes.SHA256())
        digest.update(pk.dumps(self.__dict__))
        return digest.finalize()