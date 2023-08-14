from __future__ import print_function

import Pyro4
from Pyro4 import expose, behavior


@expose
@behavior(instance_mode="single")
class SpectracsPyServer(object):
    def __init__(self):
        self.contents = ["chair", "bike", "flashlight", "laptop", "couch"]

    def getVersion(self):
        return '1.0.0'


def main():

    Pyro4.Daemon.serveSimple(
            {
                SpectracsPyServer: "sciens.SpectracsPyServer"
            },
            ns = False)

if __name__=="__main__":
    main()
