import importlib
import traceback
import os
import functools
from stix_shifter_utils.utils.module_discovery import dialect_list
from stix_shifter_utils.stix_translation.src.json_to_stix.json_to_stix import JSONToStix
from stix_shifter_utils.modules.base.stix_translation.base_data_mapper import BaseDataMapper
from stix_shifter_utils.modules.base.stix_translation.base_translator import BaseTranslator
from stix_shifter_utils.modules.base.stix_translation.base_query_translator import BaseQueryTranslator
from stix_shifter_utils.modules.base.stix_translation.base_results_translator import BaseResultTranslator
from stix_shifter_utils.modules.base.stix_transmission.base_connector import BaseConnector
from stix_shifter_utils.modules.base.stix_transmission.base_delete_connector import BaseDeleteConnector
from stix_shifter_utils.modules.base.stix_transmission.base_query_connector import BaseQueryConnector
from stix_shifter_utils.modules.base.stix_transmission.base_status_connector import BaseStatusConnector
from stix_shifter_utils.modules.base.stix_transmission.base_ping_connector import BasePingConnector
from stix_shifter_utils.modules.base.stix_transmission.base_results_connector import BaseResultsConnector

class EntryPointBase:

    def __init__(self, options):
        self.__async = True
        stack = traceback.extract_stack()
        self.__connector_module = stack[-2].filename.split('/')[-2]
        self.__dialect_to_query_translator = {}
        self.__dialect_to_results_translator = {}
        self.__dialect_to_data_mapper = {}
        self.__dialects_visible = []
        self.__dialect_default = None
        self.__options = options

        self.__results_connector = None
        self.__status_connector = None
        self.__delete_connector = None
        self.__query_connector = None

    def translation(func):
        @functools.wraps(func)
        def wrapper_func(self, *args, **kwargs):
            self.__check_translation_configured()
            return func(self, *args, **kwargs)
        return wrapper_func

    def __check_translation_configured(self):
        if not self.__dialect_default:
            raise Exception('EntryPoint: default dialect is not configured')

    def transmission(func):
        @functools.wraps(func)
        def wrapper_func(self, *args, **kwargs):
            self.__check_transmission_configured()
            return func(self, *args, **kwargs)
        return wrapper_func

    def __check_transmission_configured(self):
        if not(self.__results_connector and self.__status_connector and self.__delete_connector and self.__query_connector):
            raise Exception('EntryPoint: one of transmission connectors is not configured')

    def add_dialect(self, dialect, data_mapper=None, query_translator=None, results_translator=None, default=False, default_include=True):
        if not data_mapper:
            data_mapper = self.create_default_data_mapper(dialect)
        if not query_translator:
            query_translator = self.create_default_query_translator(dialect)
        if not results_translator:
            results_translator = self.create_default_results_translator(dialect)
        if not (isinstance(query_translator, (BaseTranslator, BaseQueryTranslator))):
            raise Exception('query_translator is not instance of BaseTranslator or BaseQueryTranslator')
        if not (isinstance(results_translator, (BaseTranslator, BaseResultTranslator))):
            raise Exception('results_translator is not instance of BaseTranslator or BaseResultTranslator')
        if data_mapper:
            if not (isinstance(data_mapper, BaseDataMapper)):
                raise Exception('data_mapper is not instance of BaseDataMapper')
        self.__dialect_to_query_translator[dialect] = query_translator
        self.__dialect_to_results_translator[dialect] = results_translator
        self.__dialect_to_data_mapper[dialect] = data_mapper
        if default:
            self.__dialect_default = dialect
        if default_include:
            self.__dialects_visible.append(dialect)
        return self

    def setup_translation_simple(self, dialect_default, query_translator=None, results_translator=None):
        module_name = self.__connector_module
        dialects = dialect_list(module_name)

        module = importlib.import_module(
                    "stix_shifter_modules." + module_name + ".stix_translation.data_mapper")
        basepath = os.path.dirname(module.__file__)
        mapping_filepath = os.path.abspath(basepath)
        for dialect in dialects:            
            data_mapper = module.DataMapper(self.__options, dialect, mapping_filepath)
            self.add_dialect(dialect, data_mapper, query_translator=query_translator, results_translator=results_translator, default=(dialect==dialect_default))

    def create_default_data_mapper(self, dialect):
        module_name = self.__connector_module
        module = importlib.import_module(
                    "stix_shifter_modules." + module_name + ".stix_translation.data_mapper")
        basepath = os.path.dirname(module.__file__)
        mapping_filepath = os.path.abspath(basepath)
        data_mapper = module.DataMapper(self.__options, dialect, mapping_filepath)
        return data_mapper

    def create_default_query_translator(self, dialect):
        module_name = self.__connector_module
        module = importlib.import_module(
                    "stix_shifter_modules." + module_name + ".stix_translation.query_translator")
        query_translator = module.QueryTranslator(dialect)
        return query_translator

    def create_default_results_translator(self, dialect):
        module_name = self.__connector_module
        module = importlib.import_module(
                    "stix_shifter_modules." + module_name + ".stix_translation.results_translator")
        basepath = os.path.dirname(module.__file__)
        mapping_filepath = os.path.abspath(basepath)
        results_translator = module.ResultsTranslator(self.__options, dialect, mapping_filepath)
        return results_translator

    @translation
    def get_mapping(self, dialect=None):
        data_mapper = self.get_data_mapper(dialect)
        results_translator = self.get_results_translator(dialect)
        mapping = {'from_stix': data_mapper.get_mapping() if data_mapper else {}, 'to_stix': results_translator.get_mapping()}
        select_fields = data_mapper.get_select_fields()
        if select_fields:
            mapping['select_fields'] = select_fields
        return mapping

    @translation
    def get_data_mapper(self, dialect=None):
        if dialect:
            return self.__dialect_to_data_mapper[dialect]
        return self.__dialect_to_data_mapper[self.__dialect_default]

    @translation    
    def get_query_translator(self, dialect=None):
        if dialect:
            return self.__dialect_to_query_translator[dialect]
        return self.__dialect_to_query_translator[self.__dialect_default]

    @translation
    def get_results_translator(self, dialect=None):
        if dialect:
            return self.__dialect_to_results_translator[dialect]
        return self.__dialect_to_results_translator[self.__dialect_default]

    @translation
    def transform_query(self, dialect, data, antlr_parsing, options, mapping=None):
        data_model_mapper = self.get_data_mapper(dialect)
        translator = self.get_query_translator(dialect)
        return translator.transform_query(data, antlr_parsing, data_model_mapper, options, mapping)

    @translation
    def translate_results(self, data_source, data, options):
        translator = self.get_results_translator()
        return translator.translate_results(data_source, data)

    @translation
    def get_dialects(self):
        return self.__dialects_visible

    def setup_transmission_basic(self, connector):
        if not isinstance(connector, BaseConnector):
            raise Exception('connector is not instance of BaseConnector')
        self.set_query_connector(connector)
        self.set_status_connector(connector)
        self.set_results_connector(connector)
        self.set_delete_connector(connector)
        self.set_ping_connector(connector)

    def set_query_connector(self, connector):
        if not (isinstance(connector, (BaseConnector, BaseQueryConnector)) or issubclass(connector, BaseConnector)):
            raise Exception('connector is not instance of BaseConnector (or it\'s subclass) or BaseQueryConnector')
        self.__query_connector = connector

    @transmission
    def create_query_connection(self, query):
        return self.__query_connector.create_query_connection(query)

    def set_status_connector(self, connector):
        if not (isinstance(connector, (BaseConnector, BaseStatusConnector)) or issubclass(connector, BaseConnector)):
            raise Exception('connector is not instance of BaseConnector (or it\'s subclass) or BaseStatusConnector')
        self.__status_connector = connector

    @transmission
    def create_status_connection(self, search_id):
        return self.__status_connector.create_status_connection(search_id)
    
    def set_results_connector(self, connector):
        if not isinstance(connector, (BaseConnector, BaseResultsConnector)):
            raise Exception('connector is not instance of BaseConnector or BaseResultsConnector')
        self.__results_connector = connector

    @transmission
    def create_results_connection(self, search_id, offset, length):
        return self.__results_connector.create_results_connection(search_id, offset, length)

    def set_delete_connector(self, connector):
        if not isinstance(connector, (BaseConnector, BaseDeleteConnector)):
            raise Exception('connector is not instance of BaseConnector or BaseDeleteConnector')
        self.__delete_connector = connector

    @transmission
    def delete_query_connection(self, search_id):
        return self.__delete_connector.delete_query_connection(search_id)

    def set_ping_connector(self, connector):
        if not isinstance(connector, (BaseConnector, BasePingConnector)):
            raise Exception('connector is not instance of BaseConnector or BasePingConnector')
        self.__ping_connector = connector

    @transmission
    def ping_connection(self):
        return self.__ping_connector.ping_connection()

    def set_async(self, is_async):
        self.__async = is_async

    def is_async(self):
        return self.__async
