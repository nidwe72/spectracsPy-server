from __future__ import print_function

from typing import Dict

import Pyro4
from Pyro4 import expose, behavior

from sciens.spectracs.logic.persistence.database.spectrometer.PersistSpectrometerLogicModule import \
    PersistSpectrometerLogicModule
from sciens.spectracs.logic.persistence.database.spectrometer.PersistenceParametersGetSpectrometers import \
    PersistenceParametersGetSpectrometers
from sciens.spectracs.model.databaseEntity.DbBase import session_factory
from sciens.spectracs.model.databaseEntity.spectral.device.Spectrometer import Spectrometer


@expose
@behavior(instance_mode="single")
class SpectracsPyServer(object):
    def __init__(self):
        pass

    def getVersion(self):
        return '1.0.0'

    def getPersistentSpectrometers(self) :
        # -> Dict[str, Spectrometer]:

        result="foo"
        print("==========2=========")
        session_factory()

        print("==========1=========")

        persistLogicModule = PersistSpectrometerLogicModule()
        persistenceParameters = PersistenceParametersGetSpectrometers()
        # entitiesByIds = persistLogicModule.getSpectrometers(persistenceParameters)
        # result = self.getEntitiesByNames(entitiesByIds)
        # print('=====result=====')
        # print(result)
        return result


def main():

    Pyro4.Daemon.serveSimple(
            {
                SpectracsPyServer: "sciens.SpectracsPyServer"
            },
            ns = False)

if __name__=="__main__":
    main()
