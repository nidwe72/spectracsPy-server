from sciens.spectracs.model.databaseEntity.DbBase import DbBaseEntityMixin


class SqlAlchemySerializer:
    pass

    @staticmethod
    def classToDict(object):
        result=None
        if isinstance(object,DbBaseEntityMixin):
            result=object.to_dict()
        return str(result)

    def dictToClass(className,dictionary):
        return None