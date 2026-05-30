import socket, time
HOST='127.0.0.1'
PORT=50001
sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
msgs=[
 "1 0 0 0 0 0 0 0 0 0 1.0 0 0 0;",
 "2 0 0 0 0 0 0 0 0 0 0.9659258 0 0 0.2588190;",
 "3 0 0 0 0 0 0 0 0 0 0.8660254 0 0 0.5;",
]
for m in msgs:
    sock.sendto(m.encode('utf-8'), (HOST, PORT))
    print('sent', m)
    time.sleep(0.5)
