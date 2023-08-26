from __future__ import print_function


from typing import Dict, List

import Pyro5
import Pyro5.serializers
from Pyro5.api import expose, behavior,callback

from sciens.spectracs.SqlAlchemySerializer import SqlAlchemySerializer
from sciens.spectracs.logic.model.util.SpectrometerUtil import SpectrometerUtil
from sciens.spectracs.logic.spectral.util.SpectralLineMasterDataUtil import SpectralLineMasterDataUtil
from sciens.spectracs.model.databaseEntity.DbBase import session_factory, app_paths
from sciens.spectracs.model.databaseEntity.spectral.device.SpectralLineMasterData import SpectralLineMasterData
from sciens.spectracs.model.databaseEntity.spectral.device.Spectrometer import Spectrometer
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerSensor import SpectrometerSensor
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerSensorChip import SpectrometerSensorChip
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerStyle import SpectrometerStyle
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerVendor import SpectrometerVendor



@behavior(instance_mode="single")
@callback
class SpectracsPyServer(object):


    # on the real server a port forwarding from sciens.at:8092 to localIp:8091 is needed:
    # iptables -t nat -A PREROUTING -p tcp -i eth0 --dport 8092 -j DNAT --to-destination 172.26.1.246:8091
    # iptables -A FORWARD -p tcp -d 172.26.1.246 --dport 8091 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT

    NAMESERVER_HOST: str = 'LOCAL'
    NAMESERVER_PORT:int=8090

    DAEMON_HOST: str = 'LOCAL'
    DAEMON_PORT:int=8091

    DAEMON_NAT_HOST: str = 'sciens.at'
    DAEMON_NAT_PORT:int=8092

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

    @staticmethod
    def configure():
        serializer = Pyro5.serializers.SerializerBase

        serializer.register_class_to_dict(Spectrometer, SqlAlchemySerializer.classToDictSpectrometer)
        className = type(Spectrometer()).__module__ + '-' + type(Spectrometer()).__name__
        serializer.register_dict_to_class(className, SqlAlchemySerializer.dictToClassSpectrometer)

        serializer.register_class_to_dict(SpectralLineMasterData,
                                          SqlAlchemySerializer.classToDictSpectralLineMasterData)
        className = type(SpectralLineMasterData()).__module__ + '-' + type(SpectralLineMasterData()).__name__
        serializer.register_dict_to_class(className, SqlAlchemySerializer.dictToClassSpectralLineMasterData)

    @expose
    def getSpectrometers(self)-> Dict[str, Spectrometer]:
        result = SpectrometerUtil().getSpectrometers()
        return result

    @expose
    def getSpectralLineMasterDatasByNames(self)-> Dict[str,SpectralLineMasterData]:
        result = SpectralLineMasterDataUtil().getSpectralLineMasterDatasByNames();
        return result

