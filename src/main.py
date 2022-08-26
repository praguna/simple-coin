'''
View & update blockchain with a simple cmd interface 
'''

help = "\nUsage : Command \ngenerate new keys using : genkey\nsend token using : send <src_key_index> <target_key_index> <amount>\nFind user's balance : balance <key_index>\nNode's view of the chain and download it in chain_{idx}.json : chain <node_index>\nExit : exit\n"

if __name__ == '__main__':
    print('Generating dummy key-pairs in keys.json,(use this to find the key_index)')
    for i in range(50): print('--', end='')
    print(help)
    
    while True:
        s = input('>')

        if s == 'genkey':
            pass

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
        

        if s == 'exit': 
            print('bye!')
            break

        print('Command not Found')
        print(help)