from stix_shifter_utils.stix_translation.src.utils.exceptions import DataMappingException
from stix_shifter_utils.modules.base.stix_translation.base_data_mapper import BaseDataMapper
from os import path


class CarDataMapper(BaseDataMapper):

    def __init__(self, options={}, dialect=None):
        super().__init__(options, dialect, path.dirname(__file__))        

    def map_object(self, stix_object_name):
        if self.map_data.get(stix_object_name):
            return self.map_data[stix_object_name]["car_type"]
        else:
            raise DataMappingException("Unable to map object `{}` into CAR".format(stix_object_name))
