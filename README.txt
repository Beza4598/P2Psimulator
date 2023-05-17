
Running Instructions

Launch Multiple Terminal Windowns and Start the Server First by running:

$ python3 FileApp.py -s <port>

Go on other terminal windows and launch as many clients as you want ensuring to use different tcp and udp
port numbers from the ones you used before.

$ python3 FileApp.py -c <name> <server-ip> <server-port>  <client-udp-port> <client-tcp-port>

Once you have clients and a server up and running, you can set the directory from which you want to offer files to
in any of the client windows by running setdir <directory> on cli.

From here you can offer and request other shared files and use list command to see all of the files currently available
for download.

When a client downloads a file it will be saved into the directory they set initially.

