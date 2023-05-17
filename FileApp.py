import sys
import re
from Client import Client
from Server import Server


def is_valid_port(port):
    port = int(port)

    return 1024 <= port <= 65535


def is_valid_ip(ip_address):
    pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

    if re.match(pattern, ip_address):
        return True
    else:
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: FileApp <mode> <command-line arguments>")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "-s":
        if len(sys.argv) != 3:
            print("Usage: FileApp -s <port>")
            sys.exit(1)

        port = int(sys.argv[2])
        server = Server(port)
        server.start()

    elif mode == "-c":
        if len(sys.argv) != 7:
            print("Usage: FileApp -c <name> <server-ip> <server-port> <client-udp-port> <client-tcp-port>")
            sys.exit(1)

        name = sys.argv[2]
        server_ip = sys.argv[3]
        server_port = int(sys.argv[4])
        udp_port = int(sys.argv[5])
        tcp_port = int(sys.argv[6])

        if not is_valid_ip(server_ip) and is_valid_port(server_port) and is_valid_port(udp_port) and is_valid_port(tcp_port):
            print("Unable to identify the ip address you entered or Invalid port number.")
            sys.exit(1)

        client = Client(name, server_ip, server_port, udp_port, tcp_port)



    else:
        print("Usage: FileApp <mode> <command-line arguments>")


if __name__ == "__main__":
    main()
