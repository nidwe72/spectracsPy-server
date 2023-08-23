from __future__ import print_function


from typing import Dict, List
from Pyro5.api import expose, behavior,callback

from sciens.spectracs.logic.model.util.SpectrometerUtil import SpectrometerUtil
from sciens.spectracs.model.databaseEntity.DbBase import session_factory, app_paths
from sciens.spectracs.model.databaseEntity.spectral.device.Spectrometer import Spectrometer
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerSensor import SpectrometerSensor
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerSensorChip import SpectrometerSensorChip
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerStyle import SpectrometerStyle
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerVendor import SpectrometerVendor


@expose
@behavior(instance_mode="single")
@callback
class SpectracsPyServer(object):

    PORT:int=8090

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
        result = SpectrometerUtil().getPersistentSpectrometers()
        print('=====result=====')
        print(result)
        return result

    def getSpectrometers(self)-> Dict[str, Spectrometer]:
        result = SpectrometerUtil().getSpectrometers()
        return result

    def syncSpectrometers(self, spectrometers: List[Spectrometer]):
        persistentSpectrometers = self.getPersistentSpectrometers()
        persistentSpectrometers=SpectrometerUtil.getEntitiesByIds(persistentSpectrometers)
        for spectrometer in spectrometers:
            if spectrometer.id not in persistentSpectrometers:
                SpectrometerUtil.saveSpectrometer(spectrometer)
                continue
