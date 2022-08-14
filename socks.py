import socket
from construct import *
import os
import threading
import select

BUFF = 1024
AUTH_REQ = Struct(
    "ver" / Const(b"\x05"),
    "nmethods" / Int8ub,
    "methods" / Array(this.nmethods, Byte)
)

AUTH_RESP = Struct(
    "ver" / Const(b"\x05"),
    "method" / Int8ub
)

AUTH_METHODS = {
    "NONE" : 0,
    "GSSAPI" : 1,
    "USERNAME_PASSWORD" : 2,
    "NONE_ACCEPTABLE" : 0xFF
}

SOCKS_REQ = Struct(
    "ver" / Const(b"\x05"),
    "cmd" / Enum(Byte, connect=b"\x01", bind=b"\x02", udp_assoc=b"\x03"),
    "rsv" / Byte,
    "atype" / Enum(Byte, v4=b"\x01", domain=b"\x03", v6=b"\x04"),
    "dst_addr" / Bytes(4),
    "dst_port" / Int16ub
)

SOCKS_RESP = Struct(
    "ver" / Const(b"\x05"),
    #Add more fields
    "rep" / Enum(Byte, success=b"\x00"),
    "rsv" / Byte,
    "atype" / Enum(Byte, v4=b"\x01", domain=b"\x03", v6=b"\x04"),
    "dst_addr" / Bytes(4),
    "dst_port" / Int16ub
)

class BreakoutException(Exception):
    pass


def start_server():
    server = socket.socket()
    server.bind(("0.0.0.0", 1080))
    server.listen()
    while True:
        client, addr = server.accept()
        target = parse_socks_req(client)
        if target != None:
            client_thread = threading.Thread(None, handle_connections, None, args=(client, target))
            client_thread.start()

def parse_socks_req(client):
    try:
        req = client.recv(BUFF)
        auth_req = AUTH_REQ.parse(req)
        for method in auth_req.methods:
            if method == AUTH_METHODS["NONE"]:
                auth_resp = AUTH_RESP.parse(b"\x05\x00")
                client.send(AUTH_RESP.build(auth_resp))
                break
        req = client.recv(BUFF)
        socks_req = SOCKS_REQ.parse(req)
        ip = socket.inet_ntoa(socks_req.dst_addr)
        port = socks_req.dst_port
        target = socket.socket()
        if(not target.connect_ex((ip, int(port)))):
            remote_ip, remote_port = target.getsockname()
            socks_resp = SOCKS_RESP.parse(b"\x05\x00\x00\x01" + socket.inet_aton(remote_ip) + socket.htons(remote_port).to_bytes(2, "big"))
            client.send(SOCKS_RESP.build(socks_resp))
        return target
    #Just generically catch any errors so the server doesn't crash
    except:
        return None

    
    
def handle_connections(client, target):
    #Create anon pipe for splicing, this improves preformance since no data is copied to usermode
    read_client, write_client = os.pipe()
    read_target, write_target = os.pipe()
    while True:
        try:
            read = [client, target]
            write = [client, target]
            err = [client, target]
            read, write, err = select.select(read, write, err)
            for s in read:
                if s == client:
                    #Socket marked as readable but no data was read means TCP "Connection Close"
                    if(not os.splice(client.fileno(), write_client, BUFF)):
                        raise BreakoutException
                    os.splice(read_client, target.fileno(), BUFF)
                else:
                    #Socket marked as readable but no data was read means TCP "Connection Close"
                    if (not os.splice(target.fileno(), write_target, BUFF)):
                        raise BreakoutException
                    os.splice(read_target, client.fileno(), BUFF)
            if err:
                raise BreakoutException
        except BreakoutException:
            client.close()
            target.close()
            return

