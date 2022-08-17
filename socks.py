import socket
from construct import *
import os
import threading
import select

PORT = 1080
PAGE_SIZE = 4096
#Size of pipe buffer in Linux kernel
BUFF = 16 * PAGE_SIZE
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


class SocksServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.active_connections = []
        self.server = socket.socket()
        #Wait 30 secconds for connections
        self.server.settimeout(30)
        self.stop_thread = False
        
    
    def run(self):
        #Simple threading wrapper
        self.start_server()
    
    def stop_server(self):
        for client_thread in self.active_connections:
            #Wait for all connections to close
            client_thread.join()
            
    def start_server(self):
        self.server.bind(("0.0.0.0", PORT))
        self.server.listen()
        while not self.stop_thread:
            try:
                client, addr = self.server.accept()
                target = self.parse_socks_req(client)
                if target != None:
                    client_thread = threading.Thread(None, self.handle_connections, None, args=(client, target))
                    self.active_connections.append(client_thread)
                    client_thread.start()
            except TimeoutError:
                #Continue if thread wasn't stopped
                continue
        self.stop_server()
        return
            
    def parse_socks_req(self, client):
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
        
    def handle_connections(self, client, target):
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
            except (BreakoutException, ConnectionResetError, BrokenPipeError):
                client.close()
                target.close()
                return

