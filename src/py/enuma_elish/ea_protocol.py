from struct import unpack, pack
from utils import err

"""
typedef struct {
    u_char tp;  // 1 byte
    u_int8_t addr_len; // 1byte
    u_int16_t port; // 2 byte
    u_int16_t payload_len; // 2byte
    u_char * addr;
    u_char * payload;
    u_int32_t checksum; // 4 byte  


} EA;
"""


def Enuma_len(data):
    return unpack(">H", data[4:6])[0]


def Enuma(data, p_hash):
    """
    password 's hash[:4]
    """
    if len(data) < 14:
        err("len wrong :{}".format(data))
        return False

    tp = data[0]
    check = tp

    addr_len = data[1]
    check ^= addr_len
    
    port, = unpack('>H', data[2:4])
    check ^= port
    
    payload_len, = unpack('>H', data[4:6])
    check ^= payload_len
    
    addr = data[6:6 + addr_len]
    payload = data[6 + addr_len:6 + addr_len + payload_len]
    checksum = data[6 + addr_len + payload_len: 6 + addr_len + payload_len + 4]
    
    checksum_int, = unpack("I", checksum)
    if checksum_int == check ^ unpack("I", p_hash)[0]:
        return tp, addr, port, payload

def Elish(tp, addr, port, payload, p_hash):
    check = tp
    pl = len(payload)
    al = len(addr)
    content = pack("B", tp)
    content += pack("B", al)
    content += pack(">H", port)
    content += pack(">H", pl)
    content += addr
    content += payload

    check ^= al
    check ^= port
    check ^= pl
    check ^= unpack("I", p_hash)[0]

    content += pack("I", check)
    # print(content)
    return content



