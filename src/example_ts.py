from transaction_and_block import *
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives._serialization import Encoding,PublicFormat
import time, pickle as pk
if __name__ == '__main__':
    private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

    data = pk.dumps({'timestamp' : int(time.time() * 1000), 'inputs' : [('rec' , 10), ('rec' , 10)], 
    'output' : 20, 'sender' : private_key.public_key().public_bytes(encoding=Encoding.OpenSSH, format=PublicFormat.OpenSSH)})

    
    hash = pk.dumps(private_key.sign(data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.MAX_LENGTH),hashes.SHA256()))

    Transaction(data , hash).verify_local()
    ts = pk.dumps([{'data' : data, 'hash' : hash}])

    Block(ts).verify_local()    