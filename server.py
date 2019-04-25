import socket
import threading
import pickle

class CI_server(object):
    def __init__(self):
        self.host_name = ''
        self.port_num = 7734
        self.active_peers = {}
        self.available_rfcs = {}

    def requestHandler(self, connection, address):
        print 'Server just accept a client, adress is ', address
        while True:
            data = connection.recv(1024)
            print '\nrequest:'
            print data,
            print 'from', address
            data = data.split('\n')
            request_method = data[0].split(' ')[0]
            #check version
            version = data[0].split(' ')[-1]
            if version != 'P2P-CI/1.0':
                connection.sendall('P2P-CI/1.0 505 P2P-CI Version Not Supported\n')
            else:
                if request_method == 'CONNECT':
                    _upload_server_port = int(data[0].split(' ')[1])
                    self.active_peers[address] = [_upload_server_port, {}]
                elif request_method == 'QUIT':
                    if self.client_quit(address):
                        break
                elif request_method == 'QUERY':
                    peer_info = pickle.dumps(self.active_peers)
                    connection.sendall(peer_info)
                elif request_method == 'ADD':
                    self.add_rfc(data, address, connection)
                elif request_method == 'LOOKUP':
                    self.client_lookup(data, connection)
                elif request_method == 'LIST':
                    self.client_list(data, connection)
                else:
                    connection.sendall('P2P-CI/1.0 400 Bad Request\n')
        connection.close()


    def client_quit(self, address):
        _quit_client = self.active_peers.pop(address)
        for _rfc in _quit_client[1]:
            rfc_index = _quit_client[1][_rfc]
            self.available_rfcs[_rfc].remove(rfc_index)
            if not self.available_rfcs[_rfc]:
                self.available_rfcs.pop(_rfc)
        return True

    def add_rfc(self, data, address, connection):
        _rfc_num = data[0].split(' ')[2]
        _new_rfc = (data[1].split(' ')[1], data[2].split(' ')[1], data[3].split(' ')[1])
        self.available_rfcs.setdefault(_rfc_num, [])
        self.available_rfcs[_rfc_num].append(_new_rfc)
        #update active_peer
        self.active_peers[address][1][_rfc_num] = _new_rfc
        #response
        data = 'P2P-CI/1.0 200 OK\n' + 'RFC %s %s %s %s\n' % (_rfc_num, _new_rfc[0], _new_rfc[1], _new_rfc[2])
        connection.sendall(data)

    def client_lookup(self, data, connection):
        _rfc_num = data[0].split(' ')[2]
        print(self.active_peers)
        print(self.available_rfcs)
        if _rfc_num in self.available_rfcs:
            data = 'P2P-CI/1.0 200 OK\n'
            #write data of this rfc into send buffer
            for record in self.available_rfcs[_rfc_num]:
                data += 'RFC %s %s %s %s\n' % (_rfc_num, record[2], record[0], record[1])
        else:
            data = 'P2P-CI/1.0 404 Not Found\n'
        connection.sendall(data)

    def client_list(self, data, connection):
        if self.available_rfcs:
            data = 'P2P-CI/1.0 200 OK\n'
            for _rfc_num in self.available_rfcs:
                for record in self.available_rfcs[_rfc_num]:
                    data += 'RFC %s %s %s %s\n' % (_rfc_num, record[2], record[0], record[1])
        else:
            data = 'P2P-CI/1.0 404 Not Found\n'
        connection.sendall(data)

    def main(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind((self.host_name, self.port_num))
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.listen(1)
        print "Server is ready!"
        while True:
            connection, address = self.serverSocket.accept()
            thread = threading.Thread(target=self.requestHandler, args=(connection, address))
            thread.start()

if __name__ == '__main__':
    server = CI_server()
    server.main()
