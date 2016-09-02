#include "libsocket.h"

static int32_t 
init_socket5(int sockfd);


static 
int32_t
init_socket5(int sockfd){
    struct timeval tmo = {0};
    int opt = 1;

    tmo.tv_sec = 2;
    tmo.tv_usec = 0;
    if (-1 == setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, (char *)&tmo, sizeof(tmo)) \
        || -1 == setsockopt(sockfd, SOL_SOCKET, SO_SNDTIMEO, (char *)&tmo, sizeof(tmo))) {
         PRINTF(LEVEL_ERROR, "setsockopt error.\n");
         return -1;
    }

#ifdef SO_NOSIGPIPE
    setsockopt(sockfd, SOL_SOCKET, SO_NOSIGPIPE, &opt, sizeof(opt));
#endif

    if (-1 == setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, (uint *)&opt, sizeof(opt))) {
        PRINTF(LEVEL_ERROR, "setsockopt SO_REUSEADDR fail.\n");
        return -1;
    }

    return 0;
}

u_char *
relay_tcp(u_char * packet){
	int sockfd = 0, n = 0, i =0;
    char recvBuff[1024];
    struct sockaddr_in serv_addr; 
    struct hostent * host_server; // host server

	iph_port * ports = IPH_PORTS(packet);
	struct ip * oldpack = EXTRACT_IP_HEAD(packet);
	struct tcphdr * tcp_header = EXTRACT_TCP_HEAD(packet);
	struct in_addr address = oldpack->ip_src;
	struct in_addr from_address = oldpack->ip_dst;
	

	// extract real data from packet;
	const u_char * payload = (const u_char *)(packet + (PAYLOAD_T(packet)));
	u_short payload_len = PAYLOAD_T_LEN(packet);
	
    bzero((char *) &serv_addr, sizeof(serv_addr));
    if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0){
        printf("\n Error : Could not create socket \n");
        return NULL;
    }

	
	if(inet_pton(AF_INET, GET_IP_DST_STR(oldpack), &serv_addr.sin_addr)<=0){
        printf("\n inet_pton error occured\n");
        return 1;
    } 
    // set address port protocol
    // serv_addr.sin_addr = address;
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = ports->dport;
    printf("=>%d\n", htons(ports->dport)); 

    if( connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0){
       printf("\n Error : Connect Failed \n");
       return NULL;
    } 

    send(sockfd, payload, payload_len, 0);
    while ( (n = read(sockfd, recvBuff, sizeof(recvBuff)-1)) > 0){
        recvBuff[n] = 0;
        if(fputs(recvBuff, stdout) == EOF){
            printf("\n Error : Fputs error\n");
        }
    } 

    if(n < 0){
        printf("\n Read error \n");
    }

    return NULL;
}