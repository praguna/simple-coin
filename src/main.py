import random
from network_local import Network
import toy_coin_client as tc
import os, shutil
'''
View & update blockchain with a simple cmd interface 
'''

help = "\nUsage : Command \ngenerate new keys using : genkey\nsend token using : send <src_key_index> (<target_key_index> <amount>)+\nFind user's balance : balance <key_index>\nNode's view of the chain at {idx} node/client : chain <node_index>\nlist keys: keys\nExit : exit\n"

if __name__ == '__main__':
    print('Generating dummy key-pairs in keys/{key_idx}.pk,(use this to find the key_index refering to a dummy user) and Starting the network...')
    if os.path.exists('keys') : shutil.rmtree('keys') # clean up
    for i in range(50): print('--', end='')
    print(help)
    n = 5 # number of miner accounts & nodes
    tc.generate_keys(n)
    network = Network(n)
    network.start()
    clients : list[tc.ToyClient] = network.get_clients() # clients attached to each node, allows network interaction
    print('keys : ', list(map(lambda e : e[:e.index('.pk')] ,os.listdir('keys'))))
    print('Creating first block with 10000 coins in each of these accounts... (No scrutiny!)\n')
    first_block = tc.zero_block() #creating coins here in the accounts to being with
    print(first_block,end='\n\n')
    print('Registering miner accounts on ',len(clients), ' nodes using the keys ...')
    for c, e in zip(clients, os.listdir('keys')): 
        c.register_as_miner(e[:e.index('.pk')])
        print(f'key_idx {c.miner_key_idx} miner at node {c.addr}')
    print('\n')
    for c in clients: c.chain.append(first_block)
    while True:
        try:
            s = input('>')

            if s == 'genkey':
                tc.generate_keys(1)
                print('keys : ', list(map(lambda e : e[:e.index('.pk')] ,os.listdir('keys'))))
                continue

            if s.split(' ')[0] == 'send': 
                L = s.split(' ')
                T = [(L[i] ,float(L[i+1])) for i in range(2, len(L), 2)]
                clients[0].register(L[1]).send_and_verifiy_transaction(T)
                continue
            
            if s.split(' ')[0] == 'balance':
                [_,pk] = s.split(' ')
                print(clients[0].register(pk).view_balance())
                continue

            if s.split(' ')[0] == 'chain':
                [_,nx] = s.split(' ')
                clients[int(nx)].print_chain()
                continue
            
            if s == 'keys':
                print('keys : ', list(map(lambda e : e[:e.index('.pk')] ,os.listdir('keys'))))
                continue

            if s == 'exit': 
                print('bye!')
                network.stop()
                break

            print('Command not Found')
            print(help)
        except Exception as e: print(e)
    if os.path.exists('keys') : shutil.rmtree('keys') #clean up