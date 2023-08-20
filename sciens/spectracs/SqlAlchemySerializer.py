from sciens.spectracs.model.databaseEntity.DbBase import DbBaseEntityMixin
from sciens.spectracs.model.databaseEntity.spectral.device.Spectrometer import Spectrometer
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerSchema import SpectrometerSchema


class SqlAlchemySerializer:
    pass

    @staticmethod
    def classToDict(object):
        result=None
        if isinstance(object,DbBaseEntityMixin):
            if isinstance(object,Spectrometer):
                result=SpectrometerSchema().dumps(object)
            else:
                result=object.to_dict()
        # return str(result)
        return result

    @staticmethod
    def dictToClass(className,dictionary):
        result = None
        if isinstance(object,DbBaseEntityMixin):
            result=None

        return result