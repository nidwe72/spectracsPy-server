from sciens.spectracs.model.databaseEntity.DbBase import DbBaseEntityMixin, SessionProvider
from sciens.spectracs.model.databaseEntity.spectral.device.Spectrometer import Spectrometer
from sciens.spectracs.model.databaseEntity.spectral.device.SpectrometerSchema import SpectrometerSchema


class SqlAlchemySerializer:
    pass

    @staticmethod
    def classToDict(object):
        result=None
        if isinstance(object,DbBaseEntityMixin):
            if isinstance(object,Spectrometer):
                result=SpectrometerSchema().dump(object)
                className = type(Spectrometer()).__module__ + '-' + type(Spectrometer()).__name__
                result['__class__']=className
            else:
                result=object.to_dict()
        # return str(result)
        return result

    @staticmethod
    def dictToClass(className,dictionary):
        result = None

        # className = 'sciens.spectracs.model.databaseEntity.spectral.device.Spectrometer-Spectrometer'
        className = dictionary['__class__']



        if className=='sciens.spectracs.model.databaseEntity.spectral.device.Spectrometer-Spectrometer':
            # session = SessionProvider().getSession()
            dictionary.pop('__class__')


            result = SpectrometerSchema(transient=True).load(dictionary,transient=True)
            # result = SpectrometerSchema().load(dictionary)
        else:
            result=None

        return result