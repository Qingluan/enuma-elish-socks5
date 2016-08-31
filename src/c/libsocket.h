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
#include "libsockettypes.h"

#ifndef GET_ETHER_TYPE
  #define GET_ETHER_TYPE( packet ) \
                ntohs( ((struct ether_header *) (packet))->ether_type )
#endif

#if __linux__
    // linux
    typedef struct iphdr ip;
#endif


#ifndef EXTRACT_IP_PACKET
  #define EXTRACT_IP_PACKET( packet) \
                (struct ip *) ((packet) + ETHER_HEAD_LEN)
#endif                

