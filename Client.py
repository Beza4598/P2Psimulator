import os
import socket
import json
import sys
import threading

from Util import dict_hash
from UserInterface import UserInterface


def remove_duplicates(li):
    return list(set(li))


stop_threads = False


class Client:

    def __init__(self, name, server_ip, server_port, client_tcp_port, client_udp_port):
        self.table = None
        self.dht = dict()
        self.name = name
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_udp_port = client_udp_port
        self.client_tcp_port = client_tcp_port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', self.client_udp_port))

        self.dir = None

        self.tcp_thread = threading.Thread(target=self.accept_tcp_connections, args=(lambda: stop_threads,))
        self.tcp_thread.start()

        self.register()

    def register(self):

        try:
            message = {"name": self.name,
                       "client_udp_port": self.client_udp_port,
                       "client_tcp_port": self.client_tcp_port}

            byt = json.dumps(message).encode('utf-8')

            self.sock.sendto(byt, (self.server_ip, self.server_port))

            server_response, addr = self.sock.recvfrom(2048)
            server_response = server_response.decode('utf-8')

            if "Error" in server_response:
                self.sock.close()
                print('Error. Unable to register client.')
                sys.exit(1)
            else:

                server_response = json.loads(server_response)
                for k, v in server_response.items():
                    self.dht[k] = {
                        'ip_address': v['ip_address'],
                        'tcp_port_number': v['client_tcp_port'],
                        'files_offered': v['files_offered']
                    }

                ack = "ACK: " + dict_hash(server_response)
                self.sock.sendto(ack.encode(), (self.server_ip, self.server_port))

            print('>>> [Welcome, You are registered.]')
            ui = UserInterface()
            ui.start_client_ui(self)

        except Exception as e:
            print("Failed to create socket or deliver registration message. Details \n" + str(e))
            sys.exit(1)

    def deregister(self, name):
        msg = {"deregister_id": name}
        byt = json.dumps(msg).encode('utf-8')

        self.sock.sendto(byt, (self.server_ip, self.server_port))

        retry_ct = 0

        while retry_ct < 2:
            ack_response, addr = self.sock.recvfrom(1024)
            ack_response = ack_response.decode()

            ack_expected = "ACK: " + dict_hash(msg)

            if ack_response == ack_expected:
                print('>>> [You are Offline. Bye.]')
                global stop_threads
                stop_threads = True
                self.tcp_thread.join()
                return

            retry_ct += 1
            self.sock.sendto(byt, (self.server_ip, self.server_port))

        print('>>> [Server not responding]')
        print('>>> [Exiting]')
        print('>>> [Server not responding]')

    def setdir(self, path):
        if os.path.isdir(path):
            if path[-1] != '/':
                path += '/'
            self.dir = path
            return '>>> [Successfully set {dir} as the directory for searching offered files.]'.format(dir=self.dir)
        else:
            return '[setdir failed: <dir> does not exist.]'

    def offer_file(self, filenames):

        if self.dir is None:
            return 'Error. Set a valid directory before offering files.'

        valid_files = {'name': self.name,
                       'files_offered':
                           [filename for filename in filenames if os.path.isfile(self.dir + filename)]}

        if len(valid_files['files_offered']) == 0:
            return 'No valid files provided please try again.'

        byt = json.dumps(valid_files).encode('utf-8')

        self.sock.sendto(byt, (self.server_ip, self.server_port))

        retry_ct = 0

        self.sock.settimeout(.5)

        while retry_ct < 2:
            ack_response, addr = self.sock.recvfrom(1024)
            ack_response = ack_response.decode()

            ack_expected = "ACK: " + dict_hash(valid_files)

            if ack_response == ack_expected:
                self.sock.settimeout(None)
                return '>>> [Offer Message received by Server.]'

            retry_ct += 1
            self.sock.sendto(byt, (self.server_ip, self.server_port))

        self.sock.settimeout(None)
        return '>>> [No ACK from Server, please try again later.]'

    def list_table(self):

        print('{:<15} {:<15} {:<15} {:<15}'.format('FILE', 'OWNER', 'IP_ADDRESS', 'TCP_PORT'))

        for k, v in self.dht.items():
            for file in v['files_offered']:
                line = '{:<15} {:<15} {:<15} {:<15}'.format(file, k, v['ip_address'], v['tcp_port_number'])
                print(line)

    def listen_to_server_updates(self):
        try:

            self.sock.settimeout(.5)
            data, address = self.sock.recvfrom(2048)
            self.sock.settimeout(None)

            data = json.loads(data.decode('utf-8'))

            if isinstance(data, dict) and data['command'] == 'OFFER':
                self.convert_to_dht(data['table'])
                print("[Received updated table from server]")

        except Exception as e:
            pass

    def request_file(self, file_name, client_name):
        if client_name not in self.dht.keys():
            print('>>> Unable to request file.')
            return

        if not (self.name == client_name) and file_name in (self.dht[client_name]['files_offered']):
            try:
                sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                addr = (self.dht[client_name]['ip_address'], self.dht[client_name]['tcp_port_number'])
                sock_tcp.connect(addr)

                print(f'< Connection with {client_name} established.>')

                msg = file_name + ':' + self.name
                sock_tcp.sendall(msg.encode())

                if self.dir is None:
                    path = file_name
                else:
                    path = self.dir + file_name
                with open(path, "wb") as f:
                    print('< Downloading ' + file_name + '...>')
                    while True:
                        data = sock_tcp.recv(1024)
                        if not data:
                            break
                        f.write(data)

                print('< ' + file_name + ' downloaded successfully.>')

                """ Closing the connection from the server. """
                sock_tcp.close()
                print(f'< Connection with {client_name} closed.>')

            except socket.error as e:
                print(">>> Caught exception socket.error : %s" % str(e))

        else:
            print('>>> Invalid File Request.')

    def accept_tcp_connections(self, stop):
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.bind(('', self.client_tcp_port))
        sock_tcp.listen(5)

        global stop_threads
        while True:
            if stop():
                break

            conn, addr = sock_tcp.accept()

            print(f'< Accepting connection request from {addr[0]}.>')

            self.serve_peer(conn)

        return None

    def serve_peer(self, conn):
        parts = (conn.recv(1024).decode()).split(':')
        filename = parts[0]
        client_name = parts[1]

        print('<Transferring ' + filename + '...>')

        file = self.dir + filename

        with open(file, 'rb') as f:
            filedata = f.read()

        conn.sendall(filedata)

        print(f'<{filename} Transferred successfully ... >')

        conn.close()
        print(f'<Connection with {client_name} closed.>')

    def find_client_name(self, addr):
        print("was here")

        for client_name, v in self.dht.items():
            tup = (v['ip_address'], v['tcp_port_number'])
            print(str(tup) + ": " + str(addr))

            if tup == addr:
                print(client_name + ' : ' + str(v))
                return client_name

        return ''

    def convert_to_dht(self, table):

        result = dict()

        for k, v in table.items():
            result[k] = {
                'ip_address': v['ip_address'],
                'tcp_port_number': v['client_tcp_port'],
                'files_offered': v['files_offered']
            }

        self.dht = result
