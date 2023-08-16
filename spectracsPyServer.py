from __future__ import print_function
import socket
import select
import sys

import Pyro4.core
import Pyro4.naming
import select

from sciens.spectracs.SpectracsPyServer import SpectracsPyServer


def main():

    spectracsPyServer = SpectracsPyServer()

    hostname='192.168.8.111'
    #hostname = '127.0.0.1'

    # ns = Pyro4.locateNS()
    nameserverUri, nameserverDaemon, broadcastServer = Pyro4.naming.startNS(host=hostname,port=8090)
    pyrodaemon = Pyro4.core.Daemon(host=hostname)

    serveruri = pyrodaemon.register(spectracsPyServer)

    print("serveruri:%s" % serveruri)
    print("nameserverUri:%s" % nameserverUri)

    nameserverDaemon.nameserver.register("sciens.spectracs.spectracsPyServer", serveruri)

    #Pyro4.Daemon.serveSimple(
    # pyrodaemon.serveSimple(
    #         {
    #             SpectracsPyServer: "sciens.SpectracsPyServer"
    #         },
    #         ns = False)

    # below is our custom event loop.
    while True:
        print("Waiting for events...")
        # create sets of the socket objects we will be waiting on
        # (a set provides fast lookup compared to a list)
        nameserverSockets = set(nameserverDaemon.sockets)

        pyroSockets = set(pyrodaemon.sockets)
        rs=[broadcastServer]  # only the broadcast server is directly usable as a select() object
        rs.extend(nameserverSockets)
        rs.extend(pyroSockets)
        rs,_,_ = select.select(rs,[],[],3)
        eventsForNameserver=[]
        eventsForDaemon=[]
        for s in rs:
            if s is broadcastServer:
                print("Broadcast server received a request")
                # broadcastServer.processRequest()
            elif s in nameserverSockets:
                eventsForNameserver.append(s)
            elif s in pyroSockets:
                eventsForDaemon.append(s)
        if eventsForNameserver:
            print("Nameserver received a request")
            nameserverDaemon.events(eventsForNameserver)
        if eventsForDaemon:
            print("Daemon received a request")
            pyrodaemon.events(eventsForDaemon)


    nameserverDaemon.close()
    broadcastServer.close()
    pyrodaemon.close()
    print("done")




if __name__=="__main__":
    main()
