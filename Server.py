import socket
import json
from Util import dict_hash


def online_entries(dict_entry):
    key, value = dict_entry

    return value['online_status']


class Server:

    def __init__(self, port):
        self.table = dict()
        self.host = "127.0.0.1"
        self.port = port
        self.sock = None

    def start(self):

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.host, self.port))

            print("Server started ...")

            self.register_client()

        except Exception as e:
            print("Failed to create socket. Details \n" + str(e))

    def register_client(self):

        while True:
            data, addr = self.sock.recvfrom(2048)
            data = json.loads(data.decode('utf-8'))

            if 'files_offered' in data:
                self.accept_files(data, addr)
            elif 'deregister_id' in data:
                self.deregister_client(data, addr)
            else:
                current_table = self.respond_to_register_request(data, addr)

                if current_table:
                    self.sock.settimeout(0.5)

                    retry_ct = 0
                    ack_received = False

                    while retry_ct < 2 and not ack_received:
                        ack_response, addr = self.sock.recvfrom(2048)
                        ack_response = ack_response.decode()

                        if ack_response == "ACK: " + dict_hash(current_table):
                            ack_received = True

                        retry_ct += 1
                        self.respond_to_register_request(data, addr)

                    self.sock.settimeout(None)

    def respond_to_register_request(self, data, addr):
        current_table = None

        if data['name'] in self.table:
            error_message = 'Error. Client already registered under this name.'.encode('utf-8')
            self.sock.sendto(error_message, addr)
            return current_table
        else:
            key = data['name']
            value = dict()

            value['ip_address'] = addr[0]
            value['client_udp_port'] = data['client_udp_port']
            value['client_tcp_port'] = data['client_tcp_port']
            value['online_status'] = True
            value['files_offered'] = list()

            self.table[key] = value

            result = dict(filter(online_entries, self.table.items()))

            table_message = json.dumps(result).encode('utf-8')
            self.sock.sendto(table_message, addr)

            current_table = self.table

            return current_table

    def accept_files(self, data, addr):
        print("Accepting files..")

        key = data['name']

        new_files_set = set(data['files_offered'])
        current_files_set = set(self.table[key]['files_offered'])

        files_to_add = list(new_files_set.difference(current_files_set))

        self.table[key]['files_offered'] += files_to_add

        ack = "ACK: " + dict_hash(data)
        self.sock.sendto(ack.encode(), addr)

        self.broadcast_table()

    def broadcast_table(self):

        self.sock.settimeout(None)

        result = dict(filter(online_entries, self.table.items()))

        offer_dht = {'command': 'OFFER',
                     'table': result}

        byt = json.dumps(offer_dht).encode('utf-8')

        for k, v in result.items():
            addr = (v['ip_address'], int(v['client_udp_port']))
            self.sock.sendto(byt, addr)


    def deregister_client(self, data, addr):

        name = data['deregister_id']
        self.table[name]['online_status'] = False

        ack = "ACK: " + dict_hash(data)
        self.sock.sendto(ack.encode(), addr)

        self.broadcast_table()
