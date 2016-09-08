import time
from Enuma_Elish.utils import err
from struct import pack, unpack

bag_head = b'GET /'
bag_tail = b' HTTP/1.0\r\nUser-Agent: w3m/0.5.3\r\nAccept: text/html, text/*;q=0.5, image/*\r\nAccept-Encoding: gzip, compress, bzip, bzip2, deflate\r\nAccept-Language: en;q=1.0\r\nHost: www.baidu.com\r\nReferer: http://www.baidu.com/s?&rqlang=cn\r\n\r\n'
BAG_LEN = 234

def invisible_air(data, stage):
    if stage == 0:
        l = pack("I", len(data))
        return bag_head + l + data + bag_tail
    elif stage == 1:
        if data[:3] == b'GET':
            l, = unpack("I", data[5:9])
            return data[9:l+9]
        elif data[:20].find(b'GET') != -1:
            i = data.find(b'GET')
            l, = unpack("I", data[5+i: 9+ i])
            return data[9+i: l+9+i]
        else:
            err("such data is urgly")
            err(data)
            return data

    


def nothing_true():
    GFW404 = """HTTP/1.1 200 OK
Cache-Control: private
Content-Length: 1885
Content-Type: text/html; charset=utf-8
Date: """ + time.asctime() + """
Server: Microsoft-IIS/7.5
X-AspNet-Version: 4.0.30319

<!DOCTYPE html><html><head><title>The resource cannot be found.</title><meta name="viewport" content="width=device-width" /><style>body {font-family:"Verdana";font-weight:normal;font-size: .7em;color:black;} p {font-family:"Verdana";font-weight:normal;color:black;margin-top: -5px}b {font-family:"Verdana";font-weight:bold;color:black;margin-top: -5px}H1 { font-family:"Verdana";font-weight:normal;font-size:18pt;color:red }H2 { font-family:"Verdana";font-weight:normal;font-size:14pt;color:maroon }pre {font-family:"Consolas","Lucida Console",Monospace;font-size:11pt;margin:0;padding:0.5em;line-height:14pt}.marker {font-weight: bold; color: black;text-decoration: none;}.version {color: gray;}.error {margin-bottom: 10px;}.expandable { text-decoration:underline; font-weight:bold; color:navy; cursor:hand; }@media screen and (max-width: 639px) {pre { width: 440px; overflow: auto; white-space: pre-wrap; word-wrap: break-word; }}@media screen and (max-width: 479px) {pre { width: 280px; }}</style></head><body bgcolor="white"><span><H1>Server Error in '/' Application.<hr width=100% size=1 color=silver></H1><h2> <i>The resource cannot be found.</i> </h2></span><font face="Arial, Helvetica, Geneva, SunSans-Regular, sans-serif "><b> Description: </b>HTTP 404. The resource you are looking for (or one of its dependencies) could have been removed, had its name changed, or is temporarily unavailable. &nbsp;Please review the following URL and make sure that it is spelled correctly.<br><br><b> Requested URL: </b>/<br><br></body></html>"""
    return GFW404.encode("utf8")