#include "libsocket.h"



int
client(int argc, char *argv[])
{
    int sockfd = 0, n = 0;
    char recvBuff[1024];
    struct sockaddr_in serv_addr; 

    if(argc != 2)
    {
        printf("\n Usage: %s <ip of server> \n",argv[0]);
        return 1;
    } 

    memset(recvBuff, '0',sizeof(recvBuff));
    if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        printf("\n Error : Could not create socket \n");
        return 1;
    } 

    memset(&serv_addr, '0', sizeof(serv_addr)); 

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(5000); 

    if(inet_pton(AF_INET, argv[1], &serv_addr.sin_addr)<=0){
        printf("\n inet_pton error occured\n");
        return 1;
    } 

    if( connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0)
    {
       printf("\n Error : Connect Failed \n");
       return 1;
    } 

    while ( (n = read(sockfd, recvBuff, sizeof(recvBuff)-1)) > 0)
    {
        recvBuff[n] = 0;
        if(fputs(recvBuff, stdout) == EOF)
        {
            printf("\n Error : Fputs error\n");
        }
    } 

    if(n < 0)
    {
        printf("\n Read error \n");
    } 

    return 0;
}





u_char *
ReadFile(char *name){
	FILE *file;
	unsigned long fileLen;
	u_char *buffer;

	//Open file
	file = fopen(name, "rb");
	if (!file){
		fprintf(stderr, "Unable to open file %s", name);
		return NULL;
	}
	
	//Get file length
	fseek(file, 0, SEEK_END);
	fileLen=ftell(file);
	

	fseek(file, 0, SEEK_SET);

	//Allocate memory
	buffer = (u_char *) malloc(sizeof(u_char) * fileLen + 1) ;
	if (!buffer){
		fprintf(stderr, "Memory error!");
        fclose(file);
		return NULL;
	}

	//Read file contents into buffer
	fread(buffer, fileLen, 1, file);
	fclose(file);

	//Do what ever with buffer
	return buffer;
}



int 
main(int argc, char const *argv[]){
	u_char * tcp_simple = ReadFile("test.bin");
	u_int16_t t = GET_ETHER_TYPE(tcp_simple);
	struct hostent * host_server;
	printf("ether header: len  %d \n", ETHER_HEAD_LEN);
	iph_port * s = IPH_PORTS(tcp_simple);
	// u_int8_t ll = (*(tcp_simple + 0xe) & 0x0f) ;
	// u_int8_t tl = (*(tcp_simple + 0x2e) >> 4   & 0x0f);
	// ll &= 0x0f;
	int ll = IP_H_LEN(tcp_simple);
	int ss = TCP_H_LEN(tcp_simple);
	printf("u %d  tl: %d  %lx \n", ll, ss, 14 + sizeof(u_int)  + sizeof(u_char));

	if (t == ETHERTYPE_IP){
		fprintf(stdout, "ip \n" );
	}

	struct ip * pack = EXTRACT_IP_HEAD(tcp_simple);
	fprintf(stdout, "vhl : %x \n", pack->ip_hl);
	fprintf(stdout, "%d\n", pack->ip_p );
	fprintf(stdout, "total len: %d\n", ntohs(pack->ip_len));
	fprintf(stdout, "off %d\n", ntohs(pack->ip_off));
	fprintf(stdout, "%s -> %s\n", strdup(GET_IP_SRC_STR(pack)), GET_IP_DST_STR(pack));
	struct tcphdr * tcp =  EXTRACT_TCP_HEAD(tcp_simple);
	fprintf(stdout, "%d -> %d\n" , ntohs(tcp->th_sport), ntohs(tcp->th_dport));
	fprintf(stdout, "length :%d\n", tcp->th_off);
	fprintf(stdout, "e 14 i %d t %d \n", IP_H_LEN(tcp_simple), TCP_H_LEN(tcp_simple) );
	fprintf(stdout, "ip : %d tcp : %d \n", PAYLOAD_T_LEN(tcp_simple), TCP_LEN(tcp_simple) );
	// fprintf(stdout, "%d -> %d" , ntohs((IPH_PORTS(tcp_simple))->sport), ntohs((IPH_PORTS(tcp_simple))->dport));
	fprintf(stdout, "%d\n", PAYLOAD_T(tcp_simple));
	// host_server = gethostbyname("http://native.qingluan.org");
	relay_tcp(tcp_simple);
	// printf("(%s)\n", host_server->h_addr);
	return 0;
}









