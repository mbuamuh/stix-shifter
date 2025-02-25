from os import path
from stix_shifter_utils.modules.base.stix_translation.base_data_mapper import BaseDataMapper


class DataMapper(BaseDataMapper):

    def map_field(self, stix_object_name, stix_property_name):
        if stix_object_name in self.map_data and stix_property_name in self.map_data[stix_object_name]["fields"]:
            return self.map_data[stix_object_name]["fields"][stix_property_name]
        else:
            return []
