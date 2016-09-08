import sys
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM 

s =  socket(AF_INET, SOCK_DGRAM)
if sys.argv[3] == "t" :
	s = socket(AF_INET, SOCK_STREAM) 
	s.connect((sys.argv[1], int(sys.argv[2])))
	s.send(b'what')
	print(s.recvfrom(8192))
	s.send(b'this >')
	print(s.recvfrom(8192))
	s.send(b'this >')
	print(s.recvfrom(8192))
	s.send(b'this >')
	print(s.recvfrom(8192))
else:
	s.sendto(b'', (sys.argv[1], int(sys.argv[2])))
	print(s.recvfrom(8192))
