from __future__ import print_function


import uuid
import Pyro5.core
import Pyro5.api
import Pyro5.nameserver
import Pyro5.serializers
import Pyro5.server
import select

from sciens.spectracs.SpectracsPyServer import SpectracsPyServer
from sciens.spectracs.SqlAlchemySerializer import SqlAlchemySerializer
from sciens.spectracs.model.databaseEntity.spectral.device.Spectrometer import Spectrometer


def main():

    spectracsPyServer = SpectracsPyServer()

    # hostname='192.168.8.111'
    hostname = '192.168.0.176'
    hostname = '172.26.1.246'


    # Pyro5.config.SERIALIZER = "json"

    Pyro5.serializers.SerializerBase.register_class_to_dict(Spectrometer,SqlAlchemySerializer.classToDict)
    className=type(Spectrometer()).__module__+'-'+type(Spectrometer()).__name__
    Pyro5.serializers.SerializerBase.register_dict_to_class(className, SqlAlchemySerializer.dictToClass)

    nameserverUri, nameserverDaemon, broadcastServer = Pyro5.api.start_ns(host=hostname,port=SpectracsPyServer.PORT)
    pyroDaemon = Pyro5.server.Daemon(host=hostname,port=8091)

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
