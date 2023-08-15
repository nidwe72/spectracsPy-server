import Pyro4

from sciens.spectracs.SpectracsPyServer import SpectracsPyServer


def main():

    SpectracsPyServer()


    Pyro4.Daemon.serveSimple(
            {
                SpectracsPyServer: "sciens.SpectracsPyServer"
            },
            ns = False)

if __name__=="__main__":
    main()
