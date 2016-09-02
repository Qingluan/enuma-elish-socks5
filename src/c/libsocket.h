#include <stdio.h>
#include <stdlib.h> 
#include <string.h>
#include <strings.h>
#include <ctype.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <netinet/if_ether.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <netdb.h>
#include <unistd.h>
#include <errno.h>



#include "libsockettypes.h"

#ifndef GET_ETHER_TYPE
  #define GET_ETHER_TYPE( packet ) \
                ntohs( ((struct ether_header *) (packet))->ether_type )
#endif

#if __linux__
    // linux
    typedef struct iphdr ip;
#endif

#define IP_H_LEN(packet) ((*((packet) + 0xe) & 0x0f) << 2)
#define TCP_H_LEN(packet) ((*((packet) + 0x2e) >> 4 & 0x0f) << 2)




#ifndef EXTRACT_IP_HEAD
  #define EXTRACT_IP_HEAD( packet) \
                (struct ip *) ((packet) + ETHER_HEAD_LEN)
#endif

#ifndef EXTRACT_TCP_HEAD
  #define EXTRACT_TCP_HEAD( packet) \
                (struct tcphdr * ) ((packet) + ETHER_HEAD_LEN + IP_HEAD_LEN)
#endif

#ifndef EXTRACT_UDP_HEAD
  #define EXTRACT_UDP_HEAD(packet) \
                (struct udphdr *) ((packet) + ETHER_HEAD_LEN + IP_HEAD_LEN )
#endif                



#ifndef GET_IP_S
  #define GET_IP_S(iphdr) \
                (iphdr)->ip_src
#endif


#ifndef GET_IP_D
  #define GET_IP_D(iphdr) \
                (iphdr)->ip_dst
#endif


#ifndef GET_IP_SRC_STR
  #define GET_IP_SRC_STR(iphdr) \
                inet_ntoa((iphdr)->ip_src)
#endif

#ifndef GET_IP_DST_STR
  #define GET_IP_DST_STR(iphdr) \
                inet_ntoa((iphdr)->ip_dst)
#endif

#define IPH_PORTS(packet) (struct iph_port *) ((packet) + ETHER_HEAD_LEN + IP_HEAD_LEN)

#ifndef IP_LEN
  #define IP_LEN(packet) (ntohs((EXTRACT_IP_HEAD(packet))->ip_len))
#endif

#ifndef UDP_LEN                
  #define UDP_LEN(packet) (ntohs(*((packet) + 0x26)  & 0xffff) )
#endif

#ifndef TCP_LEN
  #define TCP_LEN(packet) (IP_LEN(packet) -  IP_H_LEN(packet))
#endif


#ifndef _GET_PAYLOAD
  #define _GET_PAYLOAD 2


  #define PAYLOAD_T(packet) \
                    ((ETHER_HEAD_LEN) + IP_HEAD_LEN + (TCP_H_LEN(packet)))

  #define PAYLOAD_T_LEN(packet) \
                    ((TCP_LEN(packet)) - (TCP_H_LEN(packet)))

  #define PAYLOAD_U(packet) \
                    ((ETHER_HEAD_LEN) + IP_HEAD_LEN + (UDP_HEAD_LEN))

#endif


u_char *
relay_tcp(u_char * packet);