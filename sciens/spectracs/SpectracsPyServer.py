from __future__ import print_function


from typing import Dict, List

import Pyro5
import Pyro5.serializers
from Pyro5.api import expose, behavior,callback

from sciens.spectracs.SpectracsServerEndpoint import SpectracsServerEndpoint
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

    # Connection constants + Pyro serialization now live in SpectracsServerEndpoint (S7) — the shared
    # client/server contract, importable without this @expose impl. Re-exposed here so serveLocalForever and
    # the launchers (spectracsPyServer.py, service_pyro.py) keep referencing SpectracsPyServer.* unchanged.
    NAMESERVER_HOST = SpectracsServerEndpoint.NAMESERVER_HOST
    NAMESERVER_PORT = SpectracsServerEndpoint.NAMESERVER_PORT
    DAEMON_HOST = SpectracsServerEndpoint.DAEMON_HOST
    DAEMON_PORT = SpectracsServerEndpoint.DAEMON_PORT
    DAEMON_NAT_HOST = SpectracsServerEndpoint.DAEMON_NAT_HOST
    DAEMON_NAT_PORT = SpectracsServerEndpoint.DAEMON_NAT_PORT
    LOCAL_HOST = SpectracsServerEndpoint.LOCAL_HOST
    LOCAL_PORT = SpectracsServerEndpoint.LOCAL_PORT
    LOCAL_OBJECT_ID = SpectracsServerEndpoint.LOCAL_OBJECT_ID

    localUri = SpectracsServerEndpoint.localUri

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
        # Bring the SERVER database to schema head BEFORE bootstrap/seed (SPEC_schema_migrations.md §3.3,
        # policy c). This is the process that owns spectracsPyServer.db.
        from sciens.spectracs.model.databaseEntity.DatabaseInitializer import initServerDatabase
        initServerDatabase()
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

    configure = SpectracsServerEndpoint.configure

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
    def savePlugin(self, title, codeRef, version, pdfRef=None, source=None, signature=None,
                   keyId=None, author=None, targetSdkVersion=None) -> Dict:
        # MASTER: publish a plugin version — INSERT one row per (codeRef, version), never upsert (B0). A
        # published row is immutable; re-publishing an existing version is refused. The SEALED fields
        # (source/signature/keyId/author/targetSdkVersion) are signed on the master (B4) and stored verbatim;
        # the server never signs and never runs plugin code — it is a dumb store (§3).
        from sciens.spectracs.logic.persistence.database.plugin.PersistPluginLogicModule import PersistPluginLogicModule
        try:
            p = PersistPluginLogicModule().createVersion(
                title, codeRef, version, pdfRef, source, signature, keyId, author, targetSdkVersion)
        except ValueError as error:
            return {"ok": False, "message": str(error)}
        return {"ok": True, "id": p.id, "codeRef": p.codeRef, "version": p.version}

    @expose
    def getPluginSource(self, codeRef, version) -> Dict:
        # CLIENT loader (B3): return the SEALED row for (codeRef, version) so the client can verify the tuple
        # and exec the source. The server is a dumb store — it never runs plugin code; the client's shipped
        # TRUSTED_KEYS gate what it will load (SPEC_plugin_distribution.md §3 / §8, B3).
        from sciens.spectracs.logic.persistence.database.plugin.PersistPluginLogicModule import PersistPluginLogicModule
        p = PersistPluginLogicModule().findByCodeRefAndVersion(codeRef, version)
        if p is None:
            return {"ok": False, "message": "no such plugin version"}
        return {"ok": True, "codeRef": p.codeRef, "version": p.version, "title": p.title,
                "source": p.source, "signature": p.signature, "keyId": p.keyId,
                "targetSdkVersion": p.targetSdkVersion}

    @expose
    def saveSpectrometerProfile(self, serial, deviceCodeName, calibration=None, modelName=None, styleId=None,
                                lightSourceControllerType=None) -> Dict:
        # MASTER: upsert the serial-keyed profile (device + calibration) on the server. modelName + styleId pick the
        # exact spectrometer (model, camera, style), created if new; lightSourceControllerType what switches the lamp.
        from sciens.spectracs.logic.instrument.InstrumentAuthoringLogicModule import InstrumentAuthoringLogicModule
        return InstrumentAuthoringLogicModule().saveProfile(serial, deviceCodeName, calibration, modelName, styleId,
                                                            lightSourceControllerType)

    @expose
    def saveSpectrometerSetup(self, serial, pluginCodeRef, pluginVersion=None) -> Dict:
        # MASTER: bind the serial's profile to the EXACT (codeRef, version) row (B5.2/F4).
        from sciens.spectracs.logic.instrument.InstrumentAuthoringLogicModule import InstrumentAuthoringLogicModule
        return InstrumentAuthoringLogicModule().saveSetup(serial, pluginCodeRef, pluginVersion)

    @expose
    def getInstrumentCopy(self, username, password, serial) -> Dict:
        # SPEC_shelly_instrument_memory.md S2: the signed SQLite copy of one instrument for its plug. It carries
        # password hashes ⇒ only for a caller with valid credentials who is bound to `serial` or is a master.
        from sciens.spectracs.logic.instrument.InstrumentCopyLogicModule import InstrumentCopyLogicModule
        return InstrumentCopyLogicModule().buildForUser(username, password, serial)

    @expose
    def moveInstrumentToSerial(self, oldSerial, newSerial) -> Dict:
        # MASTER (S8): a replaced plug = a new serial; the calibration stays with the optics.
        from sciens.spectracs.logic.instrument.InstrumentAuthoringLogicModule import InstrumentAuthoringLogicModule
        return InstrumentAuthoringLogicModule().moveToSerial(oldSerial, newSerial)

    @expose
    def listSpectrometerProfiles(self) -> List[Dict]:
        from sciens.spectracs.logic.instrument.InstrumentAuthoringLogicModule import InstrumentAuthoringLogicModule
        return InstrumentAuthoringLogicModule().listProfiles()

    @expose
    def listSpectrometerSetups(self) -> List[Dict]:
        from sciens.spectracs.logic.instrument.InstrumentAuthoringLogicModule import InstrumentAuthoringLogicModule
        return InstrumentAuthoringLogicModule().listSetups()

    # --- payment (SPEC_paypal_payment.md §4.2) ---

    @expose
    def createPayment(self, userId) -> Dict:
        # Server sets the amount (anti-tampering); returns {ok, orderId, approvalUrl, transactionId, ...}.
        from sciens.spectracs.logic.payment.PaymentLogicModule import PaymentLogicModule
        return PaymentLogicModule().createPayment(userId)

    @expose
    def capturePayment(self, userId, orderId) -> Dict:
        from sciens.spectracs.logic.payment.PaymentLogicModule import PaymentLogicModule
        return PaymentLogicModule().capturePayment(userId, orderId)

    @expose
    def listTransactions(self, userId) -> List[Dict]:
        # Plain transaction DTOs for the logged-in user, newest first.
        from sciens.spectracs.logic.payment.PaymentLogicModule import PaymentLogicModule
        return PaymentLogicModule().listTransactions(userId)

    # --- LIMS integration (SPEC_lims_integration.md §2, L1-RPC) ----------------
    @expose
    def publishSampleToLims(self, userId, pluginLimsInfo, pdfBase64) -> Dict:
        # Create a LIMS sample for the authenticated user + attach the M2 PDF (base64). The server holds
        # the LIMS creds and fills the customer/instrument identity from the AppUser + spectrometer graph.
        from sciens.spectracs.logic.lims.LimsLogicModule import LimsLogicModule
        return LimsLogicModule().publishSample(userId, pluginLimsInfo, pdfBase64)

