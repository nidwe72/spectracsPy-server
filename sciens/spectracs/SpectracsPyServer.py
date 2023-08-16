from __future__ import print_function


from typing import Dict, List
import Pyro4
from Pyro4 import expose, behavior
from appdata import AppDataPaths

from sciens.spectracs.logic.persistence.database.spectrometer.PersistSpectrometerLogicModule import \
    PersistSpectrometerLogicModule
from sciens.spectracs.logic.persistence.database.spectrometer.PersistenceParametersGetSpectrometers import \
    PersistenceParametersGetSpectrometers
from sciens.spectracs.model.databaseEntity.DbBase import session_factory, app_paths
from sciens.spectracs.model.databaseEntity.spectral.device.Spectrometer import Spectrometer
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerSensor import SpectrometerSensor
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerSensorChip import SpectrometerSensorChip
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerStyle import SpectrometerStyle
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerVendor import SpectrometerVendor


@expose
@behavior(instance_mode="single")
class SpectracsPyServer(object):
    def __init__(self):
        self.__createBootstrapSession()

    def __createBootstrapSession(self):
        SpectrometerStyle()
        SpectrometerSensorChip()
        SpectrometerSensor()
        SpectrometerVendor()
        session = session_factory()
        session.commit()

    def getVersion(self):
        return '1.0.0'

    def getPersistentSpectrometers(self) -> Dict[str, Spectrometer]:
        persistLogicModule = PersistSpectrometerLogicModule()
        persistenceParameters = PersistenceParametersGetSpectrometers()
        result = persistLogicModule.getSpectrometers(persistenceParameters)
        # result = self.getEntitiesByNames(entitiesByIds)
        print('=====result=====')
        print(result)
        return result

    def syncSpectrometers(self,spectrometers:List[Spectrometer]):
        persistentSpectrometers = self.getPersistentSpectrometers()
        for spectrometer in spectrometers:
            spectrometer.id



