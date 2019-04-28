import socket
import sys
import threading
import random
import time
import os.path
import platform
import pickle


class Client(object):
    def __init__(self, CI_server, upload_ip):
        # init server 
        self.server_port = 7734
        self.server_name = CI_server
        # self.server_address = socket.gethostbyname(self.server_name)
        # init upload info
        #self.upload_name = socket.gethostname()
        self.upload_name = upload_ip
        self.upload_name = '192.168.140.155'
        self.upload_port = 50000 + random.randint(1,500)
        # init sockets
        self.server_socket = None
        self.upload_socket = None
        self.download_socket = None
        # upload listen flag to true
        self.client_active = True
        # print info 
        print 'Server Name: '+ self.server_name
        print 'Server Address: '+ self.server_address
        print 'Server port number: '+str(self.server_port)
        print 'Upload server name: '+self.upload_name
        print 'Upload port: '+str(self.upload_port)
    ## uploadListen
    def main(self):
        # create a thread to handle upload socket
        upload_listen = threading.Thread(target=self.uploadListen, args=())
        upload_listen.start()
        time.sleep(1)
        print'\n1. connect to server\n'
        print'2. add rfc\n'
        print'3. list all rfcs available to download\n'
        print'4. look up rfc\n'
        print'5. download rfc\n'
        print'6. get all active clients\n'
        print'7. quit\n'
        while(self.client_active):
            request = raw_input('Please input your request: ')
            if request != "1" and self.server_socket==None: 
                print"Please connect first!"
                continue 
            if request == "1":
                print"Trying to connect.."
                self.connect_to_server()
                print"Server connected successfully!"
            elif request == "2":
                self.add_rfc()
            elif request == "3":
                self.list_all_rfcs()
            elif request == "4":
                self.look_up_rfc()
            elif request == "5":
                self.download_rfc()
            elif request == "6":
                self.get_all_clients()
            elif request == "7":
                self.quit()
            else:
                print "Please input a valid number! "

    def uploadListen(self):
        self.upload_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        # self.upload_socket.bind(('',self.upload_port))
        self.upload_socket.bind((self.upload_name,self.upload_port))
        self.upload_socket.listen(10)
        while self.client_active:
            connection, address = self.upload_socket.accept()
            upload_thread = threading.Thread(target=self.buildConnection, args=(connection, address))
            upload_thread.start()
        upload_thread.join()
        self.upload_socket.close()
        print 'Upload service is closed now!'
    
    def buildConnection(self, connection, address):
        data = connection.recv(1024)
        if data == 'QUIT P2P-CI/1.0\n':
            connection.close()
        else:
            print '\nDownload request:'
            print data,
            print 'From', address
            _command = data.split('\n')[0].split(' ')[0]
            _rfc_num = data.split('\n')[0].split(' ')[2]
            _version = data.split('\n')[0].split(' ')[3]
            _rfc_path = 'rfc%s.txt' % (_rfc_num)
            if _version != 'P2P-CI/1.0':
                connection.sendall('P2P-CI/1.0 505 P2P-CI Version Not Supported\n')
            elif not os.path.exists(_rfc_path):
                connection.sendall('P2P-CI/1.0 404 Not Found\n')
            elif _command == 'GET':
                data = 'P2P-CI/1.0 200 OK\n' + 'Data: %s\n' % (time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())) + 'OS: %s\n' % (platform.platform()) + 'Last-Modified: %s\n' % (time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(os.path.getmtime(_rfc_path)))) + 'Content-Length: %s\n' % (os.path.getsize(_rfc_path)) + 'Content-Type: text/plain\n'
                connection.sendall(data)
                print 'uploading!\n'
                time.sleep(1)
                total_length = int(os.path.getsize(_rfc_path))
                current_length = 0
                rfc_file = open(_rfc_path, 'r')
                send_data = rfc_file.read(1024)
                while send_data:
                    current_length += len(send_data)
                    connection.send(send_data)
                    time.sleep(0.3)
                    send_data = rfc_file.read(1024)

                rfc_file.close()
                if current_length >= total_length:
                    print 'finish uploading!'
                else:
                    print 'upload fail, need retransimission'
            else:
                connection.sendall('P2P-CI/1.0 400 Bad Request\n')
            connection.close()
    
    def connect_to_server(self):
        # create client socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server_socket.connect((self.server_name, self.server_port))
        except BaseException, exc:
            print "Caught exception: %s" % exc
        data = 'CONNECT %s P2P-CI/1.0\n' % (str(self.upload_port))
        self.server_socket.sendall(data) 
    
    def add_rfc(self):
        rfc_num = raw_input("please input the RFC number: ")
        rfc_title = raw_input("please input the RFC title: ")
        data = 'ADD RFC %s P2P-CI/1.0\n' % (rfc_num) + 'Host: %s\n' % (socket.gethostname()) + 'Port: %s\n' % (self.upload_port) + 'Title: %s\n' % (rfc_title)
        self.server_socket.sendall(data)
        print self.server_socket.recv(1024)

    def list_all_rfcs(self):
        data = 'LIST ALL P2P-CI/1.0\n' + 'Host: %s\n' % (socket.gethostname()) + 'Port: %s\n' % (self.upload_port)
        self.server_socket.sendall(data)
        print self.server_socket.recv(1024)
    
    def look_up_rfc(self, call=0):
        rfc_num = raw_input("please input the RFC number: ")
        rfc_title = raw_input("please input the RFC title: ")
        data = 'LOOKUP RFC %s P2P-CI/1.0\n' % (rfc_num) + 'Host: %s\n' % (socket.gethostname()) + 'Port: %s\n' % (self.upload_port) + 'Title: %s\n' % (rfc_title)
        self.server_socket.sendall(data)
        data_recv = self.server_socket.recv(1024)
        if data_recv.split(" ")[1] == "404": print "There is no such rfc."
        else: 
            if not call:
                print data_recv
            else:return data_recv

    def download_rfc(self):
        data_recv = self.look_up_rfc(1)
        print(data_recv)
        rfc_num = raw_input("please input the RFC number: ")
        host_name = raw_input("please input the host name: ")
        upload_port = raw_input("please input the upload port: ")
        os_info = platform.platform()
        rfc_path = 'rfc%s.txt' % (rfc_num)
        data = 'GET RFC %s P2P-CI/1.0\n' % (rfc_num) + 'Host: %s\n' % (host_name) + 'OS: %s\n' % (os_info)
        self.download_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.download_socket.connect((host_name,int(upload_port)))
        except BaseException, exc:
            print "exception: %s" % exc
            return
        self.download_socket.sendall(data)
        recv_header = self.download_socket.recv(1024)
        print recv_header
        response = recv_header.split('\n')[0]
        if response.split(' ')[1] == '200':
            total_length = int(recv_header.split('\n')[4].split(' ')[1])
            counter = 0
            rfc_file = open(rfc_path, 'w')
            print 'start...'
            recv_content = self.download_socket.recv(1024)
            while recv_content:
                counter += len(recv_content)
                rfc_file.write(recv_content)
                print 'downloading...'
                time.sleep(0.3)
                recv_content = self.download_socket.recv(1024)
            rfc_file.close()
            print "Finished! Total length is %s"%(total_length)
        self.download_socket.close()
    
    def get_all_clients(self):
        data = 'QUERY P2P-CI/1.0\n'
        self.server_socket.sendall(data)
        print pickle.loads(self.server_socket.recv(1024))

    def quit(self):
        data = 'QUIT P2P-CI/1.0\n'
        self.server_socket.sendall(data)
        print self.server_socket.recv(1024)
        self.server_socket.close()
        self.client_active = False

if _name__ == '__main__':
    upload_ip = '192.168.140.155'
    server_ip = '192.168.140.150'
    client = Client(server_ip, upload_ip)
    client.main()

