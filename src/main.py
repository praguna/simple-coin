from network_local import Network
import toy_coin_client as tc
import os, shutil
'''
View & update blockchain with a simple cmd interface 
'''

help = "\nUsage : Command \ngenerate new keys using : genkey\nsend token using : send <src_key_index> <target_key_index> <amount>\nFind user's balance : balance <key_index>\nNode's view of the chain and download it in chain_{idx}.json : chain <node_index>\nlist keys: keys\nExit : exit\n"

if __name__ == '__main__':
    print('Generating dummy key-pairs in keys/{key_idx}.pk,(use this to find the key_index refering to a dummy user) and Starting the network...')
    if os.path.exists('keys') : shutil.rmtree('keys')
    for i in range(50): print('--', end='')
    print(help)
    tc.generate_keys()
    network = Network()
    network.start()
    clients = network.get_clients() # clients attached to each node, allows network interaction
    print('keys : ', list(map(lambda e : e[:e.index('.pk')] ,os.listdir('keys'))))
    while True:
        s = input('>')

        if s == 'genkey':
            tc.generate_keys(1)
            print('keys : ', list(map(lambda e : e[:e.index('.pk')] ,os.listdir('keys'))))
            continue

        if s.split(' ')[0] == 'send': 
            [_,sk,tk,amount] = s.split(' ')
            amount = float(amount)
            continue
        
        if s.split(' ')[0] == 'balance':
            [_,pk] = s.split(' ')
            continue

        if s.split(' ')[0] == 'chain':
            [_,nx] = s.split(' ')
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