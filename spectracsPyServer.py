from __future__ import print_function


import uuid
import Pyro5.core
import Pyro5.api
import Pyro5.nameserver
import Pyro5.serializers
import select

from sciens.spectracs.SpectracsPyServer import SpectracsPyServer
from sciens.spectracs.SqlAlchemySerializer import SqlAlchemySerializer
from sciens.spectracs.model.databaseEntity.spectral.device.Spectrometer import Spectrometer


def main():

    spectracsPyServer = SpectracsPyServer()

    hostname='192.168.8.111'

    # Pyro5.config.SERIALIZER = "json"

    Pyro5.serializers.SerializerBase.register_class_to_dict(Spectrometer,SqlAlchemySerializer.classToDict)

    nameserverUri, nameserverDaemon, broadcastServer = Pyro5.api.start_ns(host=hostname,port=8090)
    pyrodaemon = Pyro5.server.Daemon(host=hostname)

    serveruri = pyrodaemon.register(spectracsPyServer)

    print("serveruri:%s" % serveruri)
    print("nameserverUri:%s" % nameserverUri)

    nameserverDaemon.nameserver.register("sciens.spectracs.spectracsPyServer", serveruri)

    while True:
        print("Waiting for events "+str(uuid.uuid4()))
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
            pyrodaemon.events(eventsForDaemon)

    nameserverDaemon.close()
    broadcastServer.close()
    pyrodaemon.close()
    print("finished.")




if __name__=="__main__":
    main()
