from __future__ import print_function


from typing import Dict, List
from Pyro5.api import expose, behavior,callback

from sciens.spectracs.logic.model.util.SpectrometerUtil import SpectrometerUtil
from sciens.spectracs.logic.spectral.util.SpectralLineMasterDataUtil import SpectralLineMasterDataUtil
from sciens.spectracs.model.databaseEntity.DbBase import session_factory, app_paths
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

    @expose
    def getSpectrometers(self)-> Dict[str, Spectrometer]:
        result = SpectrometerUtil().getSpectrometers()
        return result

    def getSpectralLineMasterDatas(self)-> Dict[str, Spectrometer]:
        result = SpectralLineMasterDataUtil().getSpectralLineMasterDataByName()
        return result


