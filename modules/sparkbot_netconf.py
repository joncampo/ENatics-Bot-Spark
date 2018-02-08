#!/usr/bin/env python

'''
This Script gets the whole running config through yang data model and saves the file


'''
from ncclient import manager

import sys
import xml.dom.minidom
import json
import requests
'''
#################################################################################################################################################################
ENatics is a beta project about Software Defined Networking, and created by Jon Warner Campo. For any issues or concerns, you may email him at joncampo@cisco.com.
See Terms of Service - https://arcane-spire-45844.herokuapp.com/terms
See Privacy Policy - https://arcane-spire-45844.herokuapp.com/privacy
#################################################################################################################################################################
'''


# the variables below assume the user is leveraging the
# network programmability lab and accessing csr1000v
# use the IP address or hostname of your CSR1000V device
#HOST = '198.18.133.218' --> virtual-service <yang int name> of csr1kv


################### XML file to open
get_interfaces_config_file = 'modules/yang/get_interfaces.xml'
FILE2 = 'modules/yang/get_hostname.xml'

########################################################################

def netconf_get_interface(HOST,PORT,USER,PASS):

    with manager.connect(host=HOST, port=PORT, username=USER,
                    password=PASS, hostkey_verify=False,
                    device_params={'name': 'default'},
                    allow_agent=False, look_for_keys=False) as m:
        with open(get_interfaces_config_file) as f:
            return(m.get_config('running', f.read()))



########################################################################
# create a main() method
'''
def connect_device(SPARK_TOKN,room_id,search_item):
    """
    Main method that retrieves the interfaces from config via NETCONF.
    """
    with manager.connect(host=HOST, port=PORT, username=USER,
                         password=PASS, hostkey_verify=False,
                         device_params={'name': 'default'},
                         allow_agent=False, look_for_keys=False) as m:


        # print all NETCONF capabilities
        line_item=[]
        for capability in m.server_capabilities:
            #print(capability.split('?')[0])
            #print(capability.split('?')[0])
            
            line_item.append(capability.split('?')[0])
        #capability=m.server_capabilities

      

        result = m.get_config('running')
        xml_doc = xml.dom.minidom.parseString(result.xml)
        searching_xml = xml_doc.getElementsByTagName(search_item)  ####filter "data" results to all
        #hostname_xml = xml_doc.getElementsByTagName("hostname")
        
       # print(searching_xml[0].firstChild.nodeValue)
        #print(searching_xml [0].toprettyxml())
        #print(search[0].firstChild.nodeValue)
        spark_send_message(SPARK_TOKN, room_id,
                             "Below are the Yang Results of Cisco Devices: *arf* *arf* *arf* \n\n"
                             +searching_xml[0].toprettyxml())


######################################
'''

