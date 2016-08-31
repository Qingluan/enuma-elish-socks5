#include "libsocket.h"




u_char *
ReadFile(char *name)
{
	FILE *file;
	unsigned long fileLen;
	u_char *buffer;

	//Open file
	file = fopen(name, "rb");
	if (!file)
	{
		fprintf(stderr, "Unable to open file %s", name);
		return NULL;
	}
	
	//Get file length
	fseek(file, 0, SEEK_END);
	fileLen=ftell(file);
	

	fseek(file, 0, SEEK_SET);

	//Allocate memory
	buffer = (u_char *) malloc(sizeof(u_char) * fileLen + 1) ;
	if (!buffer)
	{
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



int main
(int argc, char const *argv[]){
	u_char * tcp_simple = ReadFile("tcp.pcap.bin");
	u_int16_t t = GET_ETHER_TYPE(tcp_simple);
	printf("ether header: len  %d \n", ETHER_HEAD_LEN);
	
	if (t == ETHERTYPE_IP){
		fprintf(stdout, "ip \n" );
	}
	struct ip * pack = EXTRACT_IP_PACKET(tcp_simple);
	fprintf(stdout, "%d\n", pack->ip_p );
	return 0;
}