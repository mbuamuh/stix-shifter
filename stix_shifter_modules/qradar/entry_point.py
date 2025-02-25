from stix_shifter_utils.utils.entry_point_base import EntryPointBase
from .stix_transmission.arielapiclient import APIClient
from .stix_transmission.qradar_ping_connector import QRadarPingConnector
from .stix_transmission.qradar_query_connector import QRadarQueryConnector
from .stix_transmission.qradar_status_connector import QRadarStatusConnector
from .stix_transmission.qradar_results_connector import QRadarResultsConnector
from .stix_transmission.qradar_delete_connector import QRadarDeleteConnector
from stix_shifter_utils.stix_translation.src.json_to_stix.json_to_stix import JSONToStix

import os

class EntryPoint(EntryPointBase):

    def __init__(self, connection={}, configuration={}, options={}):
        super().__init__(options)
        
        if connection:
            api_client = APIClient(connection, configuration)
            ping_connector = QRadarPingConnector(api_client)
            query_connector = QRadarQueryConnector(api_client)
            status_connector = QRadarStatusConnector(api_client)
            results_connector = QRadarResultsConnector(api_client)
            delete_connector = QRadarDeleteConnector(api_client)
            
            self.set_ping_connector(ping_connector)
            self.set_query_connector(query_connector)
            self.set_status_connector(status_connector)
            self.set_results_connector(results_connector)
            self.set_delete_connector(delete_connector)
        else:
            self.setup_translation_simple('flows')