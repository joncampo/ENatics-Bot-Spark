#!/usr/bin/python3

'''
#################################################################################################################################################################
ENatics is a beta project about Software Defined Networking, and created by Jon Warner Campo. For any issues or concerns, you may email him at joncampo@cisco.com.
See Terms of Service - https://arcane-spire-45844.herokuapp.com/terms
See Privacy Policy - https://arcane-spire-45844.herokuapp.com/privacy
#################################################################################################################################################################
'''
# Import necessary modules
from pprint import pprint
import requests
import json
import sys
import subprocess
import platform
import zipfile
import logging
import time
import os
import argparse
import re
from requests_toolbelt.multipart.encoder import MultipartEncoder
from ncclient import manager
import xml.dom.minidom

from flask import Flask, request
#####################Settings

from settings import get_settings

settings=get_settings()

BOT_SPARK_TOKEN = settings[0]
APIC_EM_BASE_URL = settings[1]
APIC_EM_USER = settings[2]
APIC_EM_PASS = settings[3]
CMX_BASE_URL = settings[4]
CMX_Auth = settings[5]
MERAKI_BASE_URL = settings[6]
MERAKI_TOKEN = settings[7]
bot_email=settings[8]
bot_name=settings[9]
HEROKU_URL=settings[10]
CSR1KV = settings[11]
NETCONF_PORT = settings[12]
NETCONF_USER = settings[13]
NETCONF_PASS = settings[14]
google_token = settings[15]

Spark_Base_URL = "https://api.ciscospark.com/v1"

#raw_cmx_list_users_container=[]
#apic_raw_result_container=[]
#raw_cmx_list_floors_container=[]
#raw_mrki_ntw_container=[]

#####################APIC-EM

from modules.sparkbot_apic_em import apic_em_getDevices, apic_em_checkStatus, apic_em_getConfig, apic_em_getDetails

#####################CMX

from modules.sparkbot_cmx import cmx_map_download, cmx_list_client, cmx_client_info, cmx_list_floors, cmx_collect_client, cmx_collect_zones, cmx_edit_map, get_floor_id

#####################meraki

from modules.sparkbot_meraki import meraki_org, meraki_network, meraki_network_devices, meraki_network_ssid

#####################netconf

from modules.sparkbot_netconf import netconf_get_interface

#####################google

from modules.sparkbot_google import googling

#####################Spark Header and API
def _spark_api(noun):

    return ''.join(('https://api.ciscospark.com/v1/', noun))
    
def _headers(bot_token):
    return {'Content-type': 'application/json',
            'Authorization': 'Bearer ' + bot_token}

def spark_send_message(token, room_id, msg):

    m = MultipartEncoder({'roomId': room_id,
						'markdown': msg,
						'files':content_file})

    r = requests.post(_spark_api('messages'), 
		data=m,
		headers={'Authorization': 'Bearer ' + token,
		'Content-Type': m.content_type})

    return r.ok

#####################Webhook Function
def webhook(bot_token, heroku_url):

	m = { "name":'ENatics', "targetUrl":heroku_url, "resource":"all", "event":"all"}
	
	r = requests.post(_spark_api('webhooks'), json=m, headers=_headers(bot_token))
	return r.ok


#######################Spark Get

def send_spark_get(end_url, payload=None, js=True):

  if payload == None:
    request = requests.get(_spark_api(end_url), headers=_headers(BOT_SPARK_TOKEN))
  else:
    request = requests.get(_spark_api(end_url), headers=_headers(BOT_SPARK_TOKEN), params=payload)
  if js == True:
    request = request.json()

  return request

#####################Business Logic
class global_command():
	def handle_text(BOT_SPARK_TOKEN, room_id,cmd, senders_email):

		result = None
		global content_file

		content_file = None

		
		cmd=cmd.lower()
		

		if 'hi' in cmd:
			result="Hi <@personEmail:"+senders_email+">"

		elif 'hello' in cmd:
			result="Hello <@personEmail:"+senders_email+">"

		elif 'thank' in cmd:
			result="Your Welcome <@personEmail:"+senders_email+">!"
		
		elif 'help' in cmd:
			result="Please see list of commands below:\n\n\n" \
			"**list devices** - shows devices managed by APIC-EM and has options for configuration and device details\n\n" \
			"**list users** - shows active users and option for location of user on map managed by CMX Location Analytics\n\n" \
			"**list floors** - shows all the floors managed by CMX Location Analytics and has 2 options: location of all the users in each floor and zones (restroom)\n\n" \
			"**list meraki** - shows meraki networks and has 2 options: devices inside a network and SSIDs\n\n" \
			"**netconf interface** - shows the netconf yang model of a cisco interface\n\n" \
			"**google <Cisco search item>** - ENatics will search the Cisco.com site for links and references of search item\n\n" \
			"**about** - information about the ENatics Bot\n\n"
			content_file=('temp/enatics.png', open('temp/enatics.png', 'rb'),'image/png')



		elif 'about' in cmd:
			result="Hello I'm ENatics! I'm here to help you manage your network easily by tapping the full potential of all the APIs inside your network! I'm currently on version 1 \n\nI'm created by Jon Warner Campo of Cisco GVE and you can reach him at joncampo@cisco.com. Your feedback is most welcome.\n\nThank you and I hope you appreciate my service! "\
			"See Terms of Service - https://arcane-spire-45844.herokuapp.com/terms\n\n"\
			"See Privacy Policy - https://arcane-spire-45844.herokuapp.com/privacy"


		elif 'network status' in cmd or 'list devices' in cmd or 'list device' in cmd:
			global apic_raw_result_container, apic_ticket
			spark_send_message(BOT_SPARK_TOKEN, room_id, "Got it <@personEmail:"+senders_email+">. Please wait.")
			ticket=apic_em_checkStatus(APIC_EM_BASE_URL,APIC_EM_USER,APIC_EM_PASS)
			
			if ticket[0]:

				apic_ticket=ticket[1]
				raw_result=apic_em_getDevices(APIC_EM_BASE_URL,apic_ticket)
				apic_raw_result_container=raw_result[1]
				welcome_text="Hi <@personEmail:"+senders_email+">, "+"Please see your requested Network Status Summary (hostname-model-status):\n"
				ending_text="\n\n\nType **config #** to get config\n\nType **details #** to get devices details"
				result=welcome_text+"\n".join(str(x) for x in raw_result[0])+ending_text

			else:
				result="\n\nFailed to Connect to APIC-EM \n\n"

		elif 'config' in cmd:
			config_text=cmd.split()
			var_num=len(config_text)-1


			try: 
				config_num=config_text[var_num]
				place_num = int(config_num) - 1
				total_device=len(apic_raw_result_container)
				test=apic_ticket
				spark_send_message(BOT_SPARK_TOKEN, room_id, "Got it <@personEmail:"+senders_email+">. Please wait.")
			except:
				result="\n\nOoops we encountered something. Please retry sending the command\n\n"
				return result

			if int(place_num) >=0 and int(place_num) < total_device:

				device_id=apic_raw_result_container[int(place_num)][str(config_num)]
				config=apic_em_getConfig(APIC_EM_BASE_URL,apic_ticket,device_id)
				config_split=config.split("\n\n\n\n\n\n\n\n")
				num=0
				while num < len(config_split):
					print (config_split[num])
					spark_send_message(BOT_SPARK_TOKEN, room_id, config_split[num])
					num=num+1
				result="End of config"


			else:
				result="\n\nPlease choose a correct number within list\n\n"
		
		elif 'details' in cmd or 'detail' in cmd:
			
			config_text=cmd.split()
			var_num=len(config_text)-1

			try: 
				config_num=config_text[var_num]
				place_num = int(config_num) - 1
				total_device=len(apic_raw_result_container)
				test=apic_ticket
				spark_send_message(BOT_SPARK_TOKEN, room_id, "Got it <@personEmail:"+senders_email+">. Please wait.")
			except:
				result="\n\nOoops we encountered something. Please retry sending the command\n\n"
				return result

			if int(place_num) >= 0 and int(place_num) < total_device:

				device_id=apic_raw_result_container[int(place_num)][str(config_num)]
				result=apic_em_getDetails(APIC_EM_BASE_URL,apic_ticket,device_id)
			else:
				result="\n\nPlease choose a correct number within list\n\n"

		elif 'list wireless devices' in cmd or 'list wireless' in cmd or 'list wireless users' in cmd or 'list users' in cmd or 'list user' in cmd:
			global raw_cmx_list_users_container
			raw_cmx_list_users=cmx_list_client(CMX_BASE_URL,CMX_Auth)
			#result=cmx_list_users
			#print (raw_cmx_list_users)
			raw_cmx_list_users_container=raw_cmx_list_users[1]

			welcome_text="Hi <@personEmail:"+senders_email+">, "+"Please see your requested Wireless Devices:\n"
			ending_text="\n\n\nType **locate user #** to get user location details"
			result=welcome_text+"\n".join(str(x) for x in raw_cmx_list_users[0])+ending_text

		elif 'list floors' in cmd or 'list floor' in cmd:
			global raw_cmx_list_floors_container
			raw_cmx_list_floors=cmx_list_floors(CMX_BASE_URL,CMX_Auth)
			#result=cmx_list_users
			#print (raw_cmx_list_floors)
			raw_cmx_list_floors_container=raw_cmx_list_floors[1]

			welcome_text="Hi <@personEmail:"+senders_email+">, "+"Please see your requested list of floors:\n"
			ending_text="\n\n\nType **floor # users** to get location of users in a floor\n\nType **floor # restroom** to get location of users in a floor"
			result=welcome_text+"\n".join(str(x) for x in raw_cmx_list_floors[0])+ending_text
		
		elif 'locate user' in cmd or 'locate device' in cmd:
			config_text=cmd.split()
			var_num=len(config_text)-1
			config_num=config_text[var_num]

			if "user" in config_num:
				result="\n\nPlease choose a correct number within list\n\n"
				return result

			try: 
				total_users=len(raw_cmx_list_users_container)
			except:
				result="\n\nOoops we encountered something. Please retry sending the command\n\n"
				return result

			if int(config_num) >= 1 and int(config_num) <= total_users:
				cmx_user=raw_cmx_list_users_container[str(config_num)]
				spark_send_message(BOT_SPARK_TOKEN, room_id, "Locating user "+cmx_user+". Please wait.")
					#print (cmx_user)
				cmx_client_details=cmx_client_info(CMX_BASE_URL,CMX_Auth,cmx_user)
				if cmx_client_details[0] is True:
					content_file=('temp/map2.png', open('temp/map2.png', 'rb'),'image/png')
					result="User "+cmx_user+" is at (Red Pin)"
			else:
				result="\n\nPlease choose a correct number within list\n\n"

		elif 'floor' in cmd:
			config_text=cmd.split()
			#print ("config")
			#print (config_text[1])
			var_num=len(config_text)-2
			var_num2=len(config_text)-1
			#if type(config_text[1]) == int:
			config_command=config_text[var_num2]
			config_num=config_text[var_num]
			#elif type(config_text[2]) == int:
			#	config_num=config_text[2]
			if "floor" in config_num:
				result="\n\nPlease choose a correct number within list\n\n"
				return result

			try: 
				total_users=len(raw_cmx_list_floors_container)

			except:
				result="\n\nOoops we encountered something. Please retry sending the command\n\n"
				return result

			if "restroom" in config_command or "restrooms" in config_command:
				if int(config_num) >= 1 and int(config_num) <= total_users:
					floor=raw_cmx_list_floors_container[str(config_num)]
					spark_send_message(BOT_SPARK_TOKEN, room_id, "Locating restroom. Please wait.")

					floor_normalized=(floor.replace(">","/"))
					cmx_floor_zones=cmx_collect_zones(CMX_BASE_URL,CMX_Auth,floor_normalized)
					if cmx_floor_zones is True:
						content_file=('temp/map2.png', open('temp/map2.png', 'rb'),'image/png')
						result="Restroom(s) (GREEN BOX) Found!"
					else:
						result="\n\nSorry No restroom in floor!\n\n"
				else:
					result="\n\nPlease choose a correct number within list\n\n"

			elif "users" in config_command or "user" in config_command:	
				
				if int(config_num) >= 1 and int(config_num) <= total_users:
					floor=raw_cmx_list_floors_container[str(config_num)]
					spark_send_message(BOT_SPARK_TOKEN, room_id, "Locating users and Downloading Map. Please wait...")

					floor_normalized=(floor.replace(">","/"))
					floor_id=get_floor_id(CMX_BASE_URL,CMX_Auth,floor_normalized)

					if floor_id[0] is True:
						print ("processing ",floor_id[1])
						cmx_floor_clients=cmx_collect_client(CMX_BASE_URL,CMX_Auth,floor_id[1])

						if cmx_floor_clients[0] is True:
							print("editing maps")
							users_x=cmx_floor_clients[1]
							users_y=cmx_floor_clients[2]
							total=len(users_x)
							#print (len(users_x),"user(s) detected!")
							spark_send_message(BOT_SPARK_TOKEN, room_id, "Processing "+str(total)+" users on map! Please wait...")

							cmx_edit=cmx_edit_map(users_x,users_y,bundle=1) 
							print ("Uploading to Spark")
							content_file=('temp/map2.png', open('temp/map2.png', 'rb'),'image/png')
							result="Number of Active Users (Red Pin) on \n\n"+floor+": "+str(total)

						else:
							result="\n\nSorry No users found!\n\n"
					else:
						result="\n\nError on Maps!\n\n"
				else:
					result="\n\nPlease choose a correct number within list\n\n"

		elif 'list meraki network' in cmd or 'list meraki networks' in cmd or 'list meraki' in cmd:
			global raw_mrki_ntw_container
			try:
				mrki_org=meraki_org(MERAKI_BASE_URL,MERAKI_TOKEN)
			except:
				result="Please check your Meraki token"

			mrki_org_id=str(mrki_org[0])
			mrki_org_name=mrki_org[1]
			print (mrki_org_id)
			raw_mrki_ntw=meraki_network(MERAKI_BASE_URL,MERAKI_TOKEN,mrki_org_id)
			raw_mrki_ntw_container=raw_mrki_ntw[1]
			welcome_text="Hi <@personEmail:"+senders_email+">!\n\n"+"Please see list of Meraki Network(s) under Organization **"+mrki_org_name+"**:\n"
			ending_text1="\n\nType **meraki # devices** to get list of Meraki Devices under chosen network."
			ending_text2="\n\nType **meraki # ssid** to get list of SSIDs under chosen network."
			result=welcome_text+"\n".join(str(x) for x in raw_mrki_ntw[0])+ending_text1+ending_text2

		elif 'meraki' in cmd:
			config_text=cmd.split()
			#print ("config")
			#print (config_text[1])
			var_num1=len(config_text)-1
			config_command=config_text[var_num1]

			var_num2=len(config_text)-2
			config_num=config_text[var_num2]
			
			if "meraki" in config_num:
				result="\n\nPlease choose a correct number within list\n\n"
				return result

			try: 
				total_users=len(raw_mrki_ntw_container)
			except:
				result="\n\nOoops we encountered something. Please retry sending the command\n\n"
				return result

			if "device" in config_command or "devices" in config_command:
				if int(config_num) >= 1 and int(config_num) <= total_users:
					meraki_network_id_chosen=raw_mrki_ntw_container[config_num]
					welcome_text="Please see list of Meraki Devices under Network ID **"+meraki_network_id_chosen+"**:\n\n"
					result=welcome_text+meraki_network_devices(MERAKI_BASE_URL,MERAKI_TOKEN,meraki_network_id_chosen)
				else:
					result="\n\nPlease choose a correct number within list\n\n"
			
			elif "ssid" in config_command or "ssids" in config_command:
				if int(config_num) >= 1 and int(config_num) <= total_users:
					meraki_network_id_chosen=raw_mrki_ntw_container[config_num]
					welcome_text="Please see list of Meraki SSIDs under Network ID **"+meraki_network_id_chosen+"**:\n\n"
					result=welcome_text+meraki_network_ssid(MERAKI_BASE_URL,MERAKI_TOKEN,meraki_network_id_chosen)
				else:
					result="\n\nPlease choose a correct number within list\n\n"
		
		elif 'netconf interface' in cmd or 'yang interface' in cmd:

			spark_send_message(BOT_SPARK_TOKEN, room_id, "Got it <@personEmail:"+senders_email+">. Please wait.")
			netconf_result_raw=netconf_get_interface(CSR1KV, NETCONF_PORT, NETCONF_USER, NETCONF_PASS)
			netconf_result=(xml.dom.minidom.parseString(netconf_result_raw.xml).toprettyxml())
			welcome_text="Hi <@personEmail:"+senders_email+">, "+"Please see your requested Netconf Interface output:\n"
			result=welcome_text+netconf_result

		elif 'reference' in cmd or 'google' in cmd:
			config_text=cmd.split()
			del config_text[0]
			search_string=" ".join(config_text)
			print (search_string)
			spark_send_message(BOT_SPARK_TOKEN, room_id, "Got it <@personEmail:"+senders_email+">. Searching for "+str(search_string)+". Please wait.")
			google_result=googling(google_token,search_string)
			print(google_result)
			welcome_text="Hi <@personEmail:"+senders_email+">, "+"Please see your requested references for "+str(search_string)+":\n\n"
			result=welcome_text+"\n\n".join(str(x) for x in google_result)


		if result == None:
			result = "I did not understand your request. Please type **help** to see what I can do"

		return result

#####################App - that waits for get or post
app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def spark_webhook():

	if request.method == 'POST':
		webhook = request.get_json(silent=True)
		resource = webhook['resource']
		senders_email = webhook['data']['personEmail']
		room_id = webhook['data']['roomId']

		msg = None
		if senders_email != bot_email:
			result = send_spark_get('messages/{0}'.format(webhook['data']['id']))  ###gets message content based on data id of webhook data

			in_message = result["text"]

			msg = global_command.handle_text(BOT_SPARK_TOKEN, room_id,in_message, senders_email)
			ending_next="\n\n*Type **help** to see what's next!*"
			
			if msg != None:
				spark_send_message(BOT_SPARK_TOKEN, room_id, msg+ending_next)
				return "true"

	elif request.method == 'GET':
		message = "<center><img src=\"http://bit.ly/SparkBot-512x512\" alt=\"Spark Bot\" style=\"width:256; height:256;\"</center>" \
		"<center><h2><b>Congratulations! Your <i style=\"color:#ff8000;\">%s</i> bot is up and running.</b></h2></center>" \
		"<center><b><i>Please don't forget to create Webhooks to start receiving events from Cisco Spark!</i></b></center>" % bot_name

		return message, 200

#####################Main Function


def main():
	app.run(debug=True)

#####################Main
if __name__ == "__main__":
	if webhook(BOT_SPARK_TOKEN, HEROKU_URL):
		print("Webhook Success!")
		main()