#ifndef ETHER_HEAD_LEN
    #define ETHER_HEAD_LEN 14
#endif

#ifndef IP_HEAD_LEN
    #define IP_HEAD_LEN 20
#endif

#ifndef TCP_HEAD_LEN
    #define TCP_HEAD_LEN 20
#endif

#ifndef UDP_HEAD_LEN
    #define UDP_HEAD_LEN 8
#endif

#ifndef ICMP_HEAD_LEN
    #define ICMP_HEAD_LEN 4
#endif

#ifndef iph_port
typedef struct iph_port{
	u_short	sport;		/* source port */
	u_short	dport;		/* destination port */
}iph_port;
#endif