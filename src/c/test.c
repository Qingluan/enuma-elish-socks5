#include "libsocket.h"




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
	u_char * tcp_simple = ReadFile("tcp.pcap.bin");
	u_int16_t t = GET_ETHER_TYPE(tcp_simple);
	printf("ether header: len  %d \n", ETHER_HEAD_LEN);
	
	if (t == ETHERTYPE_IP){
		fprintf(stdout, "ip \n" );
	}
	struct ip * pack = EXTRACT_IP_HEAD(tcp_simple);
	fprintf(stdout, "%d\n", pack->ip_p );
	fprintf(stdout, "total len: %d\n", ntohs(pack->ip_len));
	fprintf(stdout, "off %d\n", ntohs(pack->ip_off));
	fprintf(stdout, "%s -> %s\n", strdup(GET_IP_SRC_STR(pack)), GET_IP_DST_STR(pack));
	struct tcphdr * tcp =  EXTRACT_TCP_HEAD(tcp_simple);
	fprintf(stdout, "%d -> %d" , ntohs(tcp->th_sport), ntohs(tcp->th_dport));
	return 0;
}