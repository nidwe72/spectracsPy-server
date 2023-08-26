from __future__ import print_function


import uuid
import Pyro5.core
import Pyro5.api
import Pyro5.nameserver
import Pyro5.serializers
import Pyro5.server
import select

import argparse

from sciens.spectracs.SpectracsPyServer import SpectracsPyServer
from sciens.spectracs.logic.base.network.NetworkUtil import NetworkUtil

def main():

    parser = argparse.ArgumentParser(description='server for spectracs application')
    parser.add_argument('--nameserverHost', help='nameserver host',default=SpectracsPyServer.NAMESERVER_HOST)
    parser.add_argument('--nameserverPort', help='nameserver port',default=SpectracsPyServer.NAMESERVER_PORT)

    parser.add_argument('--daemonHost', help='daemon host',default=SpectracsPyServer.DAEMON_HOST)
    parser.add_argument('--daemonPort', help='daemon port',default=SpectracsPyServer.DAEMON_PORT)

    parser.add_argument('--daemonNatHost', help='daemon NAT host',default=SpectracsPyServer.DAEMON_NAT_HOST)
    parser.add_argument('--daemonNatPort', help='daemon NAT port',default=SpectracsPyServer.DAEMON_NAT_PORT)

    parser.add_argument('--local', help='flag indicating that nameserver/daemon is started on local development machine',action=argparse.BooleanOptionalAction)

    parser.add_argument('--localDaemonHost',
                        help='flag indicating that daemon.host is filled with local ip address',
                        action=argparse.BooleanOptionalAction)

    localIpAddress=NetworkUtil().getLocalIpAddress()

    args = parser.parse_args()

    nameserverHost=args.nameserverHost
    if nameserverHost=='LOCAL':
        nameserverHost=localIpAddress

    nameserverPort = args.nameserverPort

    daemonHost=args.daemonHost
    if daemonHost=='LOCAL':
        daemonHost=localIpAddress

    daemonPort = args.daemonPort

    daemonNatHost=args.daemonNatHost
    daemonNatPort = args.daemonNatPort

    local = args.local
    if local:
        daemonNatHost=None
        daemonNatPort = None

    appliedArgs={}
    appliedArgs['nameserverHost']=nameserverHost
    appliedArgs['nameserverPort'] = nameserverPort
    appliedArgs['daemonHost'] = daemonHost
    appliedArgs['daemonPort'] = daemonPort
    appliedArgs['daemonNatHost'] = daemonNatHost
    appliedArgs['daemonNatPort'] = daemonNatPort

    print('appliedArgs:')
    print(appliedArgs)

    spectracsPyServer = SpectracsPyServer()

    SpectracsPyServer.configure()

    nameserverUri, nameserverDaemon, broadcastServer = Pyro5.api.start_ns(host=nameserverHost, port=nameserverPort)
    pyroDaemon = Pyro5.server.Daemon(host=daemonHost,port=daemonPort,nathost=daemonNatHost,natport=daemonNatPort)

    serverUri = pyroDaemon.register(spectracsPyServer)

    print("serverUri:%s" % serverUri)
    print("nameserverUri:%s" % nameserverUri)

    nameserverDaemon.nameserver.register("sciens.spectracs.spectracsPyServer", serverUri)

    while True:
        print("Waiting for events "+str(uuid.uuid4()))
        # create sets of the socket objects we will be waiting on
        # (a set provides fast lookup compared to a list)
        nameserverSockets = set(nameserverDaemon.sockets)

        pyroSockets = set(pyroDaemon.sockets)
        rs=[broadcastServer]  # only the broadcast server is directly usable as a select() object
        rs.extend(nameserverSockets)
        rs.extend(pyroSockets)
        rs,_,_ = select.select(rs,[],[],3)
        eventsForNameserver=[]
        eventsForDaemon=[]
        for s in rs:
            if s is broadcastServer:
                print("broadcast server received a request")
                # broadcastServer.processRequest()
            elif s in nameserverSockets:
                eventsForNameserver.append(s)
            elif s in pyroSockets:
                eventsForDaemon.append(s)
        if eventsForNameserver:
            print("nameserver received a request")
            nameserverDaemon.events(eventsForNameserver)
        if eventsForDaemon:
            print("daemon received a request")
            pyroDaemon.events(eventsForDaemon)

    nameserverDaemon.close()
    broadcastServer.close()
    pyroDaemon.close()
    print("finished.")




if __name__=="__main__":
    main()
