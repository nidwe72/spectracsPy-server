from sciens.spectracs.model.databaseEntity.DbBase import DbBaseEntityMixin, SessionProvider
from sciens.spectracs.model.databaseEntity.spectral.device.SpectralLineMasterData import SpectralLineMasterData
from sciens.spectracs.model.databaseEntity.spectral.device.SpectralLineMasterDataSchema import \
    SpectralLineMasterDataSchema
from sciens.spectracs.model.databaseEntity.spectral.device.Spectrometer import Spectrometer
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerSchema import SpectrometerSchema


class SqlAlchemySerializer:

    @staticmethod
    def classToDictSpectrometer(object):
        result=SqlAlchemySerializer.classToDict(object)
        return result

    @staticmethod
    def classToDictSpectralLineMasterData(object):
        result=SqlAlchemySerializer.classToDict(object)
        return result

    @staticmethod
    def classToDict(object):
        result=None

        if isinstance(object,DbBaseEntityMixin):
            if isinstance(object,Spectrometer):
                result=SpectrometerSchema().dump(object)
                className = type(Spectrometer()).__module__ + '-' + type(Spectrometer()).__name__
                result['__class__']=className
            elif isinstance(object, SpectralLineMasterData):
                result=SpectralLineMasterDataSchema().dump(object)
                className = type(SpectralLineMasterData()).__module__ + '-' + type(SpectralLineMasterData()).__name__
                result['__class__']=className
            else:
                result=object.to_dict()
        return result

    @staticmethod
    def dictToClassSpectrometer(className,dictionary):
        result=SqlAlchemySerializer.dictToClass(className,dictionary)
        return result

    @staticmethod
    def dictToClassSpectralLineMasterData(className,dictionary):
        result=SqlAlchemySerializer.dictToClass(className,dictionary)
        return result


    @staticmethod
    def dictToClass(className,dictionary):
        result = None

        className = dictionary['__class__']

        if className=='sciens.spectracs.model.databaseEntity.spectral.device.Spectrometer-Spectrometer':
            dictionary.pop('__class__')
            result = SpectrometerSchema(transient=True).load(dictionary,transient=True)
        elif className=='sciens.spectracs.model.databaseEntity.spectral.device.SpectralLineMasterData-SpectralLineMasterData':
            dictionary.pop('__class__')
            result = SpectralLineMasterDataSchema(transient=True).load(dictionary,transient=True)
        else:
            result=None

        return result