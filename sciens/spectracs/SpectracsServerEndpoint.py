import Pyro5
import Pyro5.serializers

from sciens.spectracs.SqlAlchemySerializer import SqlAlchemySerializer
from sciens.spectracs.model.databaseEntity.spectral.device.SpectralLineMasterData import SpectralLineMasterData
from sciens.spectracs.model.databaseEntity.spectral.device.Spectrometer import Spectrometer


class SpectracsServerEndpoint:
    """The client<->server CONNECTION CONTRACT, split out of SpectracsPyServer (SPEC_project_structure.md S7):
    the addressing constants + the Pyro serialization setup. Imports only Pyro5, SqlAlchemySerializer and the
    two -model entities it marshals -- NOT the @expose server implementation. So the desktop client can address
    and talk to the server without importing the server's business logic (login/user-admin/payment/lims), which
    is what previously made the app unbuildable without the server impl.

    (The address is deployment config: DAEMON_NAT_HOST is the client's default connect host; a future
    user-editable server-URL app setting will override it. The server owns its own bind/NAT config.)
    """

    NAMESERVER_HOST: str = 'LOCAL'
    NAMESERVER_PORT: int = 8090

    DAEMON_HOST: str = 'LOCAL'
    DAEMON_PORT: int = 8091

    DAEMON_NAT_HOST: str = 'sciens.at'
    DAEMON_NAT_PORT: int = 8092

    # Two-app on-device model (P5/P6): a plain Pyro5 daemon on a FIXED loopback address + FIXED object id,
    # so the client builds the URI directly with NO nameserver (Pyro's UDP discovery does not cross Android
    # app sandboxes).
    LOCAL_HOST: str = '127.0.0.1'
    LOCAL_PORT: int = 8091
    LOCAL_OBJECT_ID: str = 'sciens.spectracs.spectracsPyServer'

    @classmethod
    def localUri(cls) -> str:
        return "PYRO:%s@%s:%s" % (cls.LOCAL_OBJECT_ID, cls.LOCAL_HOST, cls.LOCAL_PORT)

    @staticmethod
    def configure():
        # Register the SqlAlchemy entity (de)serializers so Pyro can marshal Spectrometer + SpectralLineMasterData
        # across the wire. Both client and server MUST run this (the client to DESERIALIZE what it receives), so it
        # is the shared contract, not per-side logic.
        serializer = Pyro5.serializers.SerializerBase

        serializer.register_class_to_dict(Spectrometer, SqlAlchemySerializer.classToDictSpectrometer)
        className = type(Spectrometer()).__module__ + '-' + type(Spectrometer()).__name__
        serializer.register_dict_to_class(className, SqlAlchemySerializer.dictToClassSpectrometer)

        serializer.register_class_to_dict(SpectralLineMasterData,
                                          SqlAlchemySerializer.classToDictSpectralLineMasterData)
        className = type(SpectralLineMasterData()).__module__ + '-' + type(SpectralLineMasterData()).__name__
        serializer.register_dict_to_class(className, SqlAlchemySerializer.dictToClassSpectralLineMasterData)
