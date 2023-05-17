class UserInterface:

    def start_client_ui(self, client):

        while True:

            client.listen_to_server_updates()
            req = input(">>> ")
            client.listen_to_server_updates()


            if req.isspace() or not req:
                continue

            parts = req.split()

            command = parts[0]

            if command == 'setdir' and len(parts) == 2:
                print(client.setdir(parts[1]))

            elif command == 'offer' and len(parts) >= 2:
                file_names = parts[1:]
                print(client.offer_file(file_names))

            elif command == 'list':
                client.list_table()

            elif command == 'dereg' and len(parts) == 2:
                client_name = parts[1]
                client.deregister(client_name)

            elif command == 'request' and len(parts) == 3:

                file_name = parts[1]
                client_name = parts[2]
                client.request_file(file_name, client_name)

            else:
                print('Unknown Command.')
                print("Usage: \n"
                      "1. setdir <dir>\n"
                      "2. offer <filename1> ...")




