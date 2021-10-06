#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""

import logging, logging.config, yaml, coloredlogs, os
import seabreeze.spectrometers as s

from opcua import Server, ua
from time import sleep
from threading import Thread

__author__ = "Giuseppe Cogoni"
__license__ = "MIT"


class WatchDog(Thread):
    def __init__(self, ser, cli, comms, timeout):
        Thread.__init__(self)
        self._stopev = False
        self.ser = ser
        self.cli = cli
        self.comms = comms
        self.to = timeout

    def stop(self):
        self._stopev = True

    def run(self):
        count = 0
        while not self._stopev:
            prev_in = self.cli.get_value()
            self.ser.set_value(prev_in^1)
            curr_in = self.cli.get_value()
            if curr_in == prev_in:
                count+=1
                sleep(1)
                if count >= self.to:
                    self.comms.set_value(False)
                else:
                    self.comms.set_value(True)                    
            else:
                count = 0
                self.comms.set_value(True)
                    


class OPCServer(object):
    """OPC Server class for the Ocean Optics instrument
    """

    def __init__(self):
        """Create logger, instrument config and OPC UA server.
        """

        self._setup_logger()
        self._get_server_parameters()
        self._get_instrument_parameters()
        self._create_opc_server()
        self._setOPCnodes()
        self._instrument_config()


    def _setup_logger(self, config_file="./logger_conf.yml"):
        """Start the logger using the provided configuration file.

        Args:
            config_file (YAML file): logger configuration file.
        """
        default_level = logging.INFO
        if os.path.exists(config_file):
            with open(config_file, "rt") as f:
                try:
                    config = yaml.safe_load(f.read())
                    logging.config.dictConfig(config)
                    coloredlogs.install()
                except Exception as e:
                    print(e)
                    print('Error in Logging Configuration. Using default configs')
                    logging.basicConfig(level=default_level)
                    coloredlogs.install(level=default_level)
        else:
            logging.basicConfig(level=default_level)
            print('Config file not found, using Default logging')
        self._logger = logging.getLogger(__name__)
        self._logger.info("Logger {} started...".format(__name__))


    def _get_server_parameters(self, config_file="./config.yml"):
        """Read and parse the yaml file containing the
        parameters to start the server. Sets the
        object attribute self._parameters.

        Args:
            configuration_file (str): Filename containing parameters formatted as yaml.
        """
        with open(config_file, "rt") as file_obj:
            self._parameters = yaml.safe_load(file_obj.read())


    def _get_instrument_parameters(self, config_file="./instrument_config.yml"):
        """Read and parse the yaml file containing the
        instrument parameters. Sets the
        object attribute self._instr_param.

        Args:
            configuration_file (str): Filename containing parameters formatted as yaml.
        """
        with open(config_file, "rt") as file_obj:
            self._instr_param = yaml.safe_load(file_obj.read())


    def _create_opc_server(self):
        """Create an OPC UA server
        """
        endpoint = self._parameters['opc']['endpoint']
        name = self._parameters['opc']['name']

        self._server = Server()
        self._server.set_endpoint(endpoint)
        self._server.set_server_name(name)
         # set all possible endpoint policies for clients to connect through
        self._server.set_security_policy([
            ua.SecurityPolicyType.NoSecurity,
            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
            ua.SecurityPolicyType.Basic256Sha256_Sign])

        uri = self._parameters['opc']['uri']
        self._server.register_namespace(uri)


    def _setOPCnodes(self):
        """Creates a dictionary with the OPC UA nodes and variat types from the
        tag parameters entered in the configuration.yml file.

        """
        nodes_dict = self._parameters['opc']['tags']
        root_node = self._parameters['opc']['root_node']
        self._logger.info('This is the client object {}'.format(nodes_dict))

        self._obj = self._server.get_objects_node()


        # OPC UA Mapping --------------------------------------------------------------
        self._OPCnodes = {}
        for tags in nodes_dict:
            for name, tag_type in tags.items():
                node = self._obj.add_variable(
                    root_node+name, 
                    name,
                    '',
                    getattr(ua.VariantType, tag_type)
                    )
                node.set_read_only()
                if tag_type in "Float":
                    node.set_value(0)
                if tag_type in "UInt32":
                    node.set_value(0)
                if tag_type in "Boolean":
                    node.set_value(False)
                if tag_type in "String":
                    node.set_value("")
                self._OPCnodes[name] = self._server.get_node(root_node+name)
        print(self._OPCnodes)
        print(self._OPCnodes['SpectraCounter'])

        self._logger.info('OPC tags created: {}'.format(self._OPCnodes))   


    def _instrument_config(self):
        devs = s.list_devices()
        if len(devs)>0:
            self._dev = devs[0]
            self._logger.info('Instrument connected: {}'.format(self._dev))
            self._serial = self._dev.serial_number
            self._model = self._dev.model
            self._spec = s.Spectrometer.from_serial_number(self._serial)
            ms = self._instr_param['ocean_optics']['integration_time']
            self._spec.integration_time_micros(ms)
            self._status = True
        else:
            self._logger.info('No instrument connected!')
            self._status = False


    def run(self):
        """Create a very simple OPC UA server.
        """
        #print(self._model)
        self._server.start()
        self._logger.info("OPC UA server started at: {}".format(
            self._parameters['opc']['endpoint']))
        count = 0
        param_capt = False
        
        wd = WatchDog(self._OPCnodes['Heartbit_s'],
                      self._OPCnodes['Heartbit_c'],
                      self._OPCnodes['Comms'],
                      self._parameters['opc']['comms_timeout'])  # WD function
        wd.start()
        
        try:
            while True:
                
                if not self._status:
                    self._instrument_config()
                
                if (self._OPCnodes['SpectraTrigger'].get_value() > 0 
                    and 
                    self._status):
                    
                    count+=1
                    
                    if not param_capt:
                        wl = self._spec.wavelengths()
                        self._OPCnodes['Wavelengths'].set_value(list(wl))
                        self._OPCnodes['DeviceModel'].set_value(self._model)
                        self._OPCnodes['DeviceSerial'].set_value(self._serial)
                        param_capt = True                        
                    
                    self._OPCnodes['Intensities'].set_value(
                        list(self._spec.intensities())
                        )
                    self._OPCnodes['SpectraCounter'].set_value(count)
                    sleep(self._instr_param['ocean_optics']['sampling_freq'])

        finally:
            wd.stop()
            self._server.stop()


#Main routine
if __name__ == "__main__":

    opcua = OPCServer()
    opcua.run()

