from __future__ import print_function


from typing import Dict, List

import Pyro5
import Pyro5.serializers
from Pyro5.api import expose, behavior,callback

from sciens.spectracs.SqlAlchemySerializer import SqlAlchemySerializer
from sciens.spectracs.logic.model.util.SpectrometerUtil import SpectrometerUtil
from sciens.spectracs.logic.spectral.util.SpectralLineMasterDataUtil import SpectralLineMasterDataUtil
from sciens.spectracs.logic.user.LoginLogicModule import LoginLogicModule
from sciens.spectracs.logic.user.UserAdminLogicModule import UserAdminLogicModule
from sciens.spectracs.logic.user.UserSeedLogicModule import UserSeedLogicModule
from sciens.spectracs.model.databaseEntity.DbBase import session_factory
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

    # Two-app on-device model (P5/P6): the server app hosts a plain Pyro5 daemon on a FIXED loopback
    # address with a FIXED object id, so the client builds the URI directly with NO nameserver
    # (Pyro's UDP-broadcast discovery does not work across Android app sandboxes).
    LOCAL_HOST: str = '127.0.0.1'
    LOCAL_PORT: int = 8091
    LOCAL_OBJECT_ID: str = 'sciens.spectracs.spectracsPyServer'

    @classmethod
    def localUri(cls) -> str:
        return "PYRO:%s@%s:%s" % (cls.LOCAL_OBJECT_ID, cls.LOCAL_HOST, cls.LOCAL_PORT)

    @classmethod
    def serveLocalForever(cls):
        """Run the server as a plain Pyro5 daemon on LOCAL_HOST:LOCAL_PORT with a fixed object id
        and NO nameserver. Blocking — the Android foreground service (P5) runs this on a non-main
        thread. Reachable at cls.localUri(). Uses selectors internally (not asyncio), so it is safe
        under Chaquopy/p4a threads."""
        import Pyro5.server
        cls.configure()
        server = cls()
        daemon = Pyro5.server.Daemon(host=cls.LOCAL_HOST, port=cls.LOCAL_PORT)
        daemon.register(server, objectId=cls.LOCAL_OBJECT_ID)
        print("SpectracsPyServer serving locally at %s" % cls.localUri())
        daemon.requestLoop()

    def __init__(self):
        self.__createBootstrapSession()
        # Seed roles + the development users (endUser/endUser, masterUser/masterUser) into the
        # separate server DB. Idempotent — safe to run on every server start.
        UserSeedLogicModule().seed()

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
        result = SpectralLineMasterDataUtil().getSpectralLineMasterDatasByNames()
        return result

    @expose
    def login(self, username, password) -> Dict:
        # Returns a plain dict {ok, userId, username, roles, message} — never the password hash.
        return LoginLogicModule().login(username, password)

    @expose
    def listUsers(self) -> List[Dict]:
        # Returns a list of plain user DTOs — never an AppUser entity, never the password hash.
        return UserAdminLogicModule().listUsers()

    @expose
    def createUser(self, username, password, displayName, enabled, roleName) -> Dict:
        return UserAdminLogicModule().createUser(username, password, displayName, enabled, roleName)

    @expose
    def updateUser(self, userId, displayName, enabled, roleName, newPassword) -> Dict:
        return UserAdminLogicModule().updateUser(userId, displayName, enabled, roleName, newPassword)

    @expose
    def deleteUser(self, userId) -> Dict:
        return UserAdminLogicModule().deleteUser(userId)

    @expose
    def setRegisteredSerial(self, userId, serial) -> Dict:
        # MASTER manual override of the user<->serial link (SPEC §11).
        return UserAdminLogicModule().setRegisteredSerial(userId, serial)

    # --- connection & calibration (SPEC_connection_and_calibration_ux.md §4) ---

    @expose
    def resolveInstrumentBySerial(self, serial) -> Dict:
        # PUBLIC: serial -> {ok, deviceCodeName, pluginCodeRef, calibration, message}.
        from sciens.spectracs.logic.instrument.InstrumentLogicModule import InstrumentLogicModule
        return InstrumentLogicModule().resolveBundle(serial)

    @expose
    def registerEndUser(self, username, password, email, firstName, lastName, serial) -> Dict:
        # PUBLIC (pre-login): create an END_USER against a master-authored serial; returns the bundle.
        from sciens.spectracs.logic.user.RegisterUserLogicModule import RegisterUserLogicModule
        return RegisterUserLogicModule().registerEndUser(username, password, email, firstName, lastName, serial)

    @expose
    def listPlugins(self) -> List[Dict]:
        # MASTER: plugin catalog as plain DTOs.
        from sciens.spectracs.logic.persistence.database.plugin.PersistPluginLogicModule import PersistPluginLogicModule
        return [{"id": p.id, "title": p.title, "codeRef": p.codeRef, "version": p.version, "pdfRef": p.pdfRef}
                for p in PersistPluginLogicModule().listPlugins()]

    @expose
    def savePlugin(self, title, codeRef, version, pdfRef=None) -> Dict:
        # MASTER: upsert a plugin (keyed on codeRef).
        from sciens.spectracs.logic.persistence.database.plugin.PersistPluginLogicModule import PersistPluginLogicModule
        p = PersistPluginLogicModule().upsert(title, codeRef, version, pdfRef)
        return {"ok": True, "id": p.id, "codeRef": p.codeRef}

    @expose
    def saveSpectrometerProfile(self, serial, deviceCodeName, calibration=None) -> Dict:
        # MASTER: upsert the serial-keyed profile (device + calibration) on the server.
        from sciens.spectracs.logic.instrument.InstrumentAuthoringLogicModule import InstrumentAuthoringLogicModule
        return InstrumentAuthoringLogicModule().saveProfile(serial, deviceCodeName, calibration)

    @expose
    def saveSpectrometerSetup(self, serial, pluginCodeRef) -> Dict:
        # MASTER: bind the serial's profile to a plugin.
        from sciens.spectracs.logic.instrument.InstrumentAuthoringLogicModule import InstrumentAuthoringLogicModule
        return InstrumentAuthoringLogicModule().saveSetup(serial, pluginCodeRef)

    @expose
    def listSpectrometerProfiles(self) -> List[Dict]:
        from sciens.spectracs.logic.instrument.InstrumentAuthoringLogicModule import InstrumentAuthoringLogicModule
        return InstrumentAuthoringLogicModule().listProfiles()

    @expose
    def listSpectrometerSetups(self) -> List[Dict]:
        from sciens.spectracs.logic.instrument.InstrumentAuthoringLogicModule import InstrumentAuthoringLogicModule
        return InstrumentAuthoringLogicModule().listSetups()

