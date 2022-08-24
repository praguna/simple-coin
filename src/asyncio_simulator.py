import asyncio
import socket


class MyProtocol(asyncio.Protocol):

    def __init__(self, on_con_lost):
        self.transport = None
        self.on_con_lost = on_con_lost

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        print("Received:", data.decode())

        # We are done: close the transport;
        # connection_lost() will be called automatically.
        self.transport.close()

    def connection_lost(self, exc):
        # The socket has been closed
        self.on_con_lost.set_result(True)
        pass


async def broadcast_main(msg = 'F'):
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()

    # for 1 node broadcast blocks to 5 nodes
    sp, pcs = [], []

    for _ in range(1):
        r,w = socket.socketpair()
        t, p = await loop.create_connection(
        lambda: MyProtocol(on_con_lost), sock=r)
        sp.append((r, w))
        pcs.append(p)
    
    # Simulate the reception of data from the network.
    for i in range(1): loop.call_soon(w.send, f'{msg}abc{i+1}\n'.encode())
    
    try:
        await pcs[0].on_con_lost
    except: pass

if __name__ == '__main__':
    asyncio.run(broadcast_main())