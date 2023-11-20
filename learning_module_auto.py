from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.ofproto import ofproto_v1_3
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet, ethernet
from ryu.lib import hub
from ryu.ofproto import ether
from ryu.lib.packet import ethernet, arp, packet, ipv4

from operator import attrgetter
#import os
import time, datetime
import re

class LearningModuleAuto(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

	def __init__(self, *args, **kwargs):
		super(LearningModuleAuto, self).__init__(*args, **kwargs)
		self.mac_to_port = {}
		self.datapaths = {}
		self.monitor_thread = hub.spawn(self._monitor)
		
		self.start_t = 0.0
		self.ingress_port_counter = {}

		self.temp = {}
		self.Bps_rec = {}
		self.new_timer = True

		# Time policy attributes
		self.activate_time_restrict = datetime.time(23, 59, 30)
		self.deact_time_restrict = datetime.time(0, 0, 30)
		self.is_flow_table_empty = False
		self.passed_zero = False

		# Smart learning attributes
		self.entity = {
						'10.0.0.1':{
									'credit':datetime.timedelta(hours=0, minutes=0, seconds=0),
									'edu_site':['10.0.0.2'] ,
									'entmt_site':['10.0.0.3'],
									'credit_ratio':{'incr':1.0, 'decr':1.0},
									'prev_conn_to_edu':False,
									'prev_conn_time':datetime.datetime.now()
								  },
								  
						#'10.0.0.6':{
						#			'credit':datetime.timedelta(hours=0, minutes=0, seconds=0),
						#			'edu_site':['10.0.0.3', '10.0.0.5'] ,
						#			'entmt_site':['10.0.0.2', '10.0.0.4'],
						#			'credit_ratio':{'incr':2.0, 'decr':1.0},
						#			'prev_conn_to_edu':False,
						#			'prev_conn_time':datetime.datetime.now()
						#			}
					  }
		
		self.ip_mac_ref = {}
		self.scan_mode = True
		self.scan_timer = datetime.datetime
		self.scan_lock = False
		self.scan_result = []
		self.add_edu_site = False
		self.add_entmt_site = True
	
	@set_ev_cls(ofp_event.EventOFPStateChange,
		 [MAIN_DISPATCHER, DEAD_DISPATCHER])
	def _state_change_handler(self, ev):
			datapath = ev.datapath
			if ev.state == MAIN_DISPATCHER:
				if not datapath.id in self.datapaths:
					self.logger.debug('register datapath: %016x', datapath.id)
					self.datapaths[datapath.id] = datapath
			elif ev.state == DEAD_DISPATCHER:
				if datapath.id in self.datapaths:
					self.logger.debug('unregister datapath: %016x', datapath.id)
					del self.datapaths[datapath.id]
	
	def _monitor(self):
		while True:
			for dp in self.datapaths.values():
				self._request_stats(dp)
			hub.sleep(1)
	
	def _request_stats(self, datapath):
		self.logger.debug('send stats request: %016x', datapath.id)
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		if self.new_timer:
			self.start_t = time.time()
			self.new_timer = False
		
		req = parser.OFPFlowStatsRequest(datapath)
		datapath.send_msg(req)

		req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
		datapath.send_msg(req)

		if self.scan_lock == False and self.scan_mode == True:
			match = parser.OFPMatch()
			actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
			self.add_flow(datapath, 0, match, actions, 1, 1)

			self.add_goto_table_flow(datapath, 0, match, 0, 1, 99)
			self.scan_timer = datetime.datetime.now()
			self.scan_lock = True
		
		elif self.scan_mode == True and (datetime.datetime.now() - self.scan_timer).total_seconds() >= 8.0:
			self.scan_mode = False
			self.scan_lock = False 
			# add new flow
			
			self.logger.info("Finish scanning !!!!! The result is:")
			self.logger.info('=' * 40)
			self.logger.info('in-port  out-port  bytes' + ' '*15 +'|')
			self.logger.info('-------- -------- -------- ' + ' '*12 + '|')

			if self.scan_result != []:
				#self.logger.info(self.scan_result)
				for i in range(2):
					self.logger.info('%8x %8x %8d' + ' ' * 13 + '|',
										self.scan_result[i].match['in_port'],
										self.scan_result[i].instructions[0].actions[0].port,
										self.scan_result[i].byte_count)
					match = parser.OFPMatch(in_port=self.scan_result[i].match['in_port'], eth_dst=self.scan_result[i].match['eth_dst'])
					actions = [parser.OFPActionOutput(self.scan_result[i].instructions[0].actions[0].port)]
					self.add_flow(datapath, 1, match, actions, 8)

					# Add respective IP
					src_port = self.scan_result[i].match['in_port']
					src_mac = next(mac for mac, port in self.mac_to_port[datapath.id].items() if port == src_port)
					src_ip = next(ip for ip, mac in self.ip_mac_ref.items() if mac == src_mac)
					dst_mac = self.scan_result[i].match['eth_dst']
					dst_ip = next(ip for ip, mac in self.ip_mac_ref.items() if mac == dst_mac)

					if self.add_edu_site == True and self.add_entmt_site == True:
						self.add_edu_site = False
						self.add_entmt_site = False

					if src_ip in self.entity.keys():
						if  dst_ip not in self.entity[src_ip]['edu_site'] and self.add_edu_site == True:
							self.entity[src_ip]['edu_site'].append(dst_ip)
							self.add_edu_site = False

						elif dst_ip not in self.entity[src_ip]['entmt_site'] and self.add_entmt_site == True:
							self.entity[src_ip]['entmt_site'].append(dst_ip)
							self.add_entmt_site = False

			self.logger.info('=' * 40)

			self.delete_all_flows(datapath, 1, 1)
			self.delete_all_flows(datapath, 99, 0)

		#else:

		
		for target_entity in self.entity:
			current_entity = self.entity[target_entity]
			if (current_entity['credit'] + datetime.timedelta(seconds= (-1 * current_entity['credit_ratio']['decr']))).total_seconds() >= 0 and current_entity['prev_conn_to_edu'] == False:
				self.unblock_entmt_sites(target_entity, current_entity['entmt_site'], datapath)
			
			else:
				self.block_entmt_sites(target_entity, current_entity['entmt_site'], datapath)

		#if (self.learning_time + datetime.timedelta(seconds= (-1 * self.credit_ratio['decr']))).total_seconds() >= 0 and self.previously_connect_to_edu == False: #self.learning_time.total_seconds() > 0
			"""actions = [parser.OFPActionOutput(3)]
			match = parser.OFPMatch(in_port=1, eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:03')
			self.mod_flow(datapath, match, actions)"""

		#	self.unblock_entmt_sites(self.entertainment_sites, datapath)
		#	self.send_arp_request(datapath, "00:00:00:00:00:01", "10.0.0.1",
		#	 "00:00:00:00:00:03", "10.0.0.3", 3)
			
			

		#else:
		#	self.block_entmt_sites(self.entertainment_sites, datapath)

		# Intervial restriction
		#
		now_time = datetime.datetime.now()   #time.strftime("%H:%M:%S")
		cur_time = now_time.strftime("%H:%M:%S")

		hr = int(cur_time[:2])
		mins = int(cur_time[3:5])
		sec = int(cur_time[6:])

		self.logger.info(f"current time: {hr}:{mins}:{sec}")
		
	
	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def switch_features_handler(self, ev):
		datapath = ev.msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		
		#match = parser.OFPMatch()
		#actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
		#				  ofproto.OFPCML_NO_BUFFER)]

		# miss-flow entry
		#self.add_flow(datapath, 0, match, actions)

		# delete LLDP flow
		self.establish_ip_mac_ref()

		# install arp flow in each host 
		self.deliver_arp(datapath)
		
		# preinstall flow entries in switch 
		self.load_flows(datapath)

		for target_entity in self.entity:
			self.block_entmt_sites(target_entity, self.entity[target_entity]['entmt_site'], datapath)
		#self.block_entmt_sites(self.entertainment_sites, datapath)

	def deliver_arp(self, datapath):
		self.send_arp_request(datapath, "00:00:00:00:00:01", "10.0.0.1",
			 "00:00:00:00:00:02", "10.0.0.2", 2)
		self.send_arp_request(datapath, "00:00:00:00:00:02", "10.0.0.2",
			 "00:00:00:00:00:01", "10.0.0.1", 1)
		self.send_arp_request(datapath, "00:00:00:00:00:01", "10.0.0.1",
			 "00:00:00:00:00:03", "10.0.0.3", 3)
		self.send_arp_request(datapath, "00:00:00:00:00:03", "10.0.0.3",
			 "00:00:00:00:00:01", "10.0.0.1", 1)
		self.send_arp_request(datapath, "00:00:00:00:00:02", "10.0.0.2",
			 "00:00:00:00:00:03", "10.0.0.3", 3)
		self.send_arp_request(datapath, "00:00:00:00:00:03", "10.0.0.3",
			 "00:00:00:00:00:02", "10.0.0.2", 2)
		
		self.send_arp_request(datapath, "00:00:00:00:00:01", "10.0.0.1",
			 "00:00:00:00:00:04", "10.0.0.4", 4)
		self.send_arp_request(datapath, "00:00:00:00:00:04", "10.0.0.4",
			 "00:00:00:00:00:01", "10.0.0.1", 1)
		self.send_arp_request(datapath, "00:00:00:00:00:01", "10.0.0.1",
			 "00:00:00:00:00:05", "10.0.0.5", 5)
		self.send_arp_request(datapath, "00:00:00:00:00:05", "10.0.0.5",
			 "00:00:00:00:00:01", "10.0.0.1", 1)
		"""self.send_arp_request(datapath, "00:00:00:00:00:06", "10.0.0.6",
			 "00:00:00:00:00:02", "10.0.0.2", 2)
		self.send_arp_request(datapath, "00:00:00:00:00:06", "10.0.0.6",
			 "00:00:00:00:00:03", "10.0.0.3", 3)
		self.send_arp_request(datapath, "00:00:00:00:00:06", "10.0.0.6",
			 "00:00:00:00:00:04", "10.0.0.4", 4)
		self.send_arp_request(datapath, "00:00:00:00:00:06", "10.0.0.6",
			 "00:00:00:00:00:05", "10.0.0.5", 5)
		self.send_arp_request(datapath, "00:00:00:00:00:05", "10.0.0.5",
			 "00:00:00:00:00:06", "10.0.0.6", 6)
		self.send_arp_request(datapath, "00:00:00:00:00:04", "10.0.0.4",
			 "00:00:00:00:00:06", "10.0.0.6", 6)
		self.send_arp_request(datapath, "00:00:00:00:00:03", "10.0.0.3",
			 "00:00:00:00:00:06", "10.0.0.6", 6)
		self.send_arp_request(datapath, "00:00:00:00:00:02", "10.0.0.2",
			 "00:00:00:00:00:06", "10.0.0.6", 6)"""
		

	# Reinstall flows after being deleted
	def load_flows(self, datapath):
		self.preinstall_flow(1, "00:00:00:00:00:01", "00:00:00:00:00:02",
			   1, 2, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:02", "00:00:00:00:00:01",
			   2, 1, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:02", "00:00:00:00:00:03",
			   2, 3, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:03", "00:00:00:00:00:02",
			   3, 2, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:01", "00:00:00:00:00:03",
			   1, 3, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:03", "00:00:00:00:00:01",
			   3, 1, datapath)
		
		"""self.preinstall_flow(1, "00:00:00:00:00:01", "00:00:00:00:00:04",
			   1, 4, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:01", "00:00:00:00:00:05",
			   1, 5, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:04", "00:00:00:00:00:01",
			   4, 1, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:05", "00:00:00:00:00:01",
			   5, 1, datapath)"""
		
		"""self.preinstall_flow(1, "00:00:00:00:00:06", "00:00:00:00:00:02",
			   6, 2, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:06", "00:00:00:00:00:03",
			   6, 3, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:06", "00:00:00:00:00:04",
			   6, 4, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:06", "00:00:00:00:00:05",
			   6, 5, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:02", "00:00:00:00:00:06",
			   2, 6, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:03", "00:00:00:00:00:06",
			   3, 6, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:04", "00:00:00:00:00:06",
			   4, 6, datapath)
		self.preinstall_flow(1, "00:00:00:00:00:05", "00:00:00:00:00:06",
			   5, 6, datapath)"""
		
	def preinstall_flow(self, datapath_id, src, dst, in_port, 
			 out_port, datapath): #, ev
		#msg = ev.msg
		#datapath = msg.datapath
		ofp_parser = datapath.ofproto_parser
		self.mac_to_port.setdefault(datapath_id, {})
		self.mac_to_port[datapath_id][src] = in_port

		cookie = 7
		actions = [ofp_parser.OFPActionOutput(out_port)]
		match = ofp_parser.OFPMatch(in_port = in_port, eth_dst = dst
				  , eth_src = src)
		
		self.add_flow(datapath, 1, match, actions, cookie)
		self.logger.info("preinstall flow %s %s %s %s", datapath_id, 
		   src, dst ,in_port)

		data = None
		out = ofp_parser.OFPPacketOut(datapath=datapath, buffer_id=datapath.ofproto.OFP_NO_BUFFER,
										in_port=in_port, actions=actions, data=data)
		datapath.send_msg(out)
	
	def add_flow(self, datapath, priority, match, actions, cookie = 1, table_id = 0):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
		mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
		 match=match, instructions=inst, cookie=cookie, table_id=table_id)

		datapath.send_msg(mod)

	def add_goto_table_flow(self, datapath, priority, match, table_id, to_table_id,cookie = 1):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		inst = [parser.OFPInstructionGotoTable(to_table_id)]
		mod = parser.OFPFlowMod(datapath=datapath, priority=priority, 
						  match=match, instructions=inst, cookie=cookie, table_id=table_id)
		datapath.send_msg(mod)

	def mod_flow(self, datapath, match, action = []):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		#action = [parser.OFPActionOutput(ofproto.OFPP_ANY)]
				
		inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, action)]

		mod = parser.OFPFlowMod(
			datapath=datapath,
			priority=1,
			command=ofproto.OFPFC_MODIFY, 
			match=match,
			instructions=inst)
		
		datapath.send_msg(mod)

	
	def delete_all_flows(self, datapath, cookie, table_id, cookie_mask=0xFFFFFFFFFFFFFFFF):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		command = ofproto_v1_3.OFPFC_DELETE
		
		delete_msg = parser.OFPFlowMod(
			datapath=datapath,
			cookie=cookie,
			cookie_mask=cookie_mask,
			table_id=table_id, #ofproto.OFPTT_ALL
			command=command,
			out_port=ofproto.OFPP_ANY,
			out_group=ofproto.OFPG_ANY,
		)

		datapath.send_msg(delete_msg)

	def establish_ip_mac_ref(self):
		self.ip_mac_ref.setdefault("10.0.0.1", "00:00:00:00:00:01")
		self.ip_mac_ref.setdefault("10.0.0.2", "00:00:00:00:00:02")
		self.ip_mac_ref.setdefault("10.0.0.3", "00:00:00:00:00:03")
		self.ip_mac_ref.setdefault("10.0.0.4", "00:00:00:00:00:04")
		self.ip_mac_ref.setdefault("10.0.0.5", "00:00:00:00:00:05")
		#self.ip_mac_ref.setdefault("10.0.0.6", "00:00:00:00:00:06")

	def send_arp_request(self, datapath, src_mac, src_ip, dst_mac, dst_ip, out_port):
		e = ethernet.ethernet(dst_mac, src_mac, ethertype=ether.ETH_TYPE_ARP)
		a = arp.arp(1, 0x0800, 6, 4, 1, src_mac, src_ip
		  , dst_mac, dst_ip)
		p = packet.Packet()
		p.add_protocol(e)
		p.add_protocol(a)
		p.serialize()

		actions = [datapath.ofproto_parser.OFPActionOutput(out_port, 0)]
		out = datapath.ofproto_parser.OFPPacketOut(
			datapath = datapath,
			buffer_id = datapath.ofproto.OFP_NO_BUFFER , #0xffffffff
			in_port = datapath.ofproto.OFPP_CONTROLLER,
			actions = actions,
			data = p.data
		)
		datapath.send_msg(out)

	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
			msg = ev.msg
			datapath = msg.datapath
			ofproto = datapath.ofproto
			parser = datapath.ofproto_parser
			in_port = msg.match['in_port']

			pkt = packet.Packet(msg.data)
			eth = pkt.get_protocols(ethernet.ethernet)[0]
			
			dst = eth.dst
			src = eth.src

			dpid = datapath.id
			self.mac_to_port.setdefault(dpid, {})

			self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)
			
			if self.mac_to_port[dpid].get(src) == None:
				self.mac_to_port[dpid][src] = in_port

			if dst in self.mac_to_port[dpid]:
				out_port = self.mac_to_port[dpid][dst]
			else:
				out_port = ofproto.OFPP_FLOOD
			# construct action list.
			actions = [parser.OFPActionOutput(out_port)]

			# install a flow to avoid packet_in next time.
			if out_port != ofproto.OFPP_FLOOD:
				match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
				self.add_flow(datapath, 1, match, actions, 1, 1)

			# construct packet_out message and send it.
			out = parser.OFPPacketOut(datapath=datapath,
									buffer_id=ofproto.OFP_NO_BUFFER,
									in_port=in_port, actions=actions,
									data=msg.data)
			datapath.send_msg(out)

	# Functions to implement smart learning
	def block_entmt_sites(self, src_ip, list_of_entmt, datapath):
		parser = datapath.ofproto_parser

		eth_src = self.ip_mac_ref[src_ip]
		in_port = self.mac_to_port[datapath.id][eth_src]

		for site_ip in list_of_entmt:
			eth_dst = self.ip_mac_ref[site_ip]
			match = parser.OFPMatch(in_port=in_port, eth_src=eth_src, eth_dst=eth_dst)
			self.mod_flow(datapath, match)

			match = parser.OFPMatch(in_port=in_port, eth_dst=eth_dst)
			self.mod_flow(datapath, match)
	
	def unblock_entmt_sites(self, src_ip, list_of_entmt, datapath):
		parser = datapath.ofproto_parser
		
		eth_src = self.ip_mac_ref[src_ip]
		in_port = self.mac_to_port[datapath.id][eth_src]

		for site_ip in list_of_entmt:
			eth_dst = self.ip_mac_ref[site_ip]
			match = parser.OFPMatch(in_port=in_port, eth_src=eth_src, eth_dst=eth_dst)
			actions = [parser.OFPActionOutput(self.mac_to_port[datapath.id][eth_dst])]
			self.mod_flow(datapath, match, actions)

			self.send_arp_request(datapath, eth_src, src_ip, eth_dst, site_ip, self.mac_to_port[datapath.id][eth_dst])
		
	@set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
	def _flow_stats_reply_handler(self, ev):
		body = ev.msg.body
		datapath = ev.msg.datapath
		#os.system("clear")
		#self.logger.info(body)
		#self.logger.info(ev.msg)
		#end_t = time.time()

		for target_entity in self.entity:
			cur_entity_credit = self.entity[target_entity]['credit'].total_seconds()
			cur_entity = self.entity[target_entity]

			self.logger.info("=" * 44)
			self.logger.info(target_entity + " Credit: %.2f" , cur_entity_credit) if \
				cur_entity_credit != int(cur_entity_credit) else \
					self.logger.debug(target_entity + " Credit: %d" ,cur_entity_credit)

			last_conn_time = cur_entity['prev_conn_time'].strftime("%H:%M:%S")
			self.logger.debug(f"{target_entity} Latest connection time {last_conn_time}")
			self.logger.debug(f"edu_site: {cur_entity['edu_site']}, entmt_site: {cur_entity['entmt_site']}")
			self.logger.info("=" * 44)

		self.logger.info('Table 0')
		self.logger.info('datapath         '
						 'in-port  eth-dst           '
						 'out-port packets  bytes')
		self.logger.info('---------------- '
						 '-------- ----------------- '
						 '-------- -------- -------- ')
		#try:
		
		# delete specific LLDP flow
		self.delete_all_flows(datapath, 0, 0)
		#print(body)
		res = sorted([flow for flow in body if flow.priority != 0 and flow.table_id == 0],
							key=lambda flow: (flow.match['in_port'],flow.match['eth_dst']))
		for stat in res:
				#self.logger.info(stat)
				'''
				self.logger.info('%016x %8x %17s %8x %8d %8d',
									ev.msg.datapath.id,
									stat.match['in_port'], stat.match['eth_dst'],
									stat.instructions[0].actions[0].port,
									stat.packet_count, stat.byte_count)
				'''
				# Determine whether there is a value in the "action" field of the flow or not
				# Yes:
				# Store it in "temp" dict
				if stat.instructions:
					self.temp[str(stat.match['in_port']) + " " + stat.match['eth_dst']] = {"datapath":ev.msg.datapath.id, 
																							"out_port":stat.instructions[0].actions[0].port,
																							"packets":stat.packet_count,
																							"bytes":stat.byte_count,
																							}
				# No:
				else:
					self.temp[str(stat.match['in_port']) + " " + stat.match['eth_dst']] = {"datapath":ev.msg.datapath.id, 
																							"out_port":"X",
																							"packets":stat.packet_count,
																							"bytes":stat.byte_count,
																							}
				class Found(Exception): pass
				try:
					for each_entity in self.entity.keys():
						cur_entity = self.entity[each_entity]
						for each_site in (cur_entity['edu_site'] + cur_entity['entmt_site']):
							in_port = self.mac_to_port[datapath.id][self.ip_mac_ref[each_entity]]
							eth_dst = self.ip_mac_ref[each_site]
							if ((stat.match['in_port'] == in_port) and (stat.match['eth_dst'] == eth_dst)):
								port_to_mac = str(stat.match['in_port']) + ">" + str(stat.match['eth_dst'])
								self.ingress_port_counter.setdefault(port_to_mac, stat.byte_count)
								raise Found
				except Found:
					pass

				
					
				#port_to_mac = str(stat.match['in_port']) + ">" + str(stat.match['eth_dst'])
				
				#if port_to_mac not in self.ingress_port_counter:
				"""self.ingress_port_counter.setdefault(port_to_mac, stat.byte_count)"""

				for target_entity in self.entity:
					cur_entity = self.entity[target_entity]
					t_diff = datetime.datetime.now() - cur_entity['prev_conn_time']
					if t_diff.total_seconds() > 3:
						cur_entity['prev_conn_to_edu'] = False

					src_port = stat.match['in_port']
					src_mac = next(mac for mac, port in self.mac_to_port[datapath.id].items() if port == src_port)
					#stat.match.get('eth_src') != None and stat.match['eth_src']
					if  self.ip_mac_ref[target_entity] == src_mac:
						# Inverse lookup for ip in the dict "self.ip_mac_ref"
						dst_ip = next(ip for ip, mac in self.ip_mac_ref.items() if mac == stat.match['eth_dst'])
						if dst_ip in cur_entity['edu_site'] and stat.byte_count - self.ingress_port_counter[port_to_mac] > 0:
							cur_entity['credit'] += datetime.timedelta(seconds= (1 * cur_entity['credit_ratio']['incr']))
							self.ingress_port_counter[port_to_mac] = stat.byte_count
							cur_entity['prev_conn_time'] = datetime.datetime.now()
							cur_entity['prev_conn_to_edu'] = True

							self.block_entmt_sites(target_entity, cur_entity['entmt_site'], datapath)
						
						elif dst_ip in cur_entity['entmt_site'] and stat.byte_count - self.ingress_port_counter[port_to_mac] > 0:
							if (cur_entity['credit'] + datetime.timedelta(seconds= (-1 * cur_entity['credit_ratio']['decr']))).total_seconds() >= 0:
								cur_entity['credit'] += datetime.timedelta(seconds= (-1 * cur_entity['credit_ratio']['decr']))
								self.ingress_port_counter[port_to_mac] = stat.byte_count
						
							else:
								self.block_entmt_sites(target_entity, cur_entity['entmt_site'], datapath)

				"""if stat.match['eth_dst'] ==  '00:00:00:00:00:02' and stat.byte_count - self.ingress_port_counter[port_to_mac] > 0: #end_t - self.start_t >= 1.0
						self.learning_time += datetime.timedelta(seconds= (1 * self.credit_ratio['incr']))
						self.ingress_port_counter[port_to_mac] = stat.byte_count
						self.previously_conn_time = datetime.datetime.now()
						self.previously_connect_to_edu = True

						self.block_entmt_sites(self.entertainment_sites, datapath)
					
					#self.new_timer = True
				#else:
				#	pass
					#self.logger.info(f"{port_to_mac} Bps: {self.Bps_rec[port_to_mac]}")
				elif stat.match['eth_dst'] == '00:00:00:00:00:03' and stat.byte_count - self.ingress_port_counter[port_to_mac] > 0:
						if (self.learning_time + datetime.timedelta(seconds= (-1 * self.credit_ratio['decr']))).total_seconds() >= 0:
							self.learning_time += datetime.timedelta(seconds= (-1 * self.credit_ratio['decr']))
							self.ingress_port_counter[port_to_mac] = stat.byte_count
						
						else:
							self.block_entmt_sites(self.entertainment_sites, datapath)"""

						

		#except IndexError:
		
		#self.logger.debug(self.ingress_port_counter)
		for rec in self.temp:
				#self.logger.info(type(rec))

				inPort_dstMac = rec.split()
				self.logger.info('%016x %8s %17s %8s %8d %8d',
									self.temp[rec]['datapath'],
									inPort_dstMac[0],inPort_dstMac[1],
									self.temp[rec]['out_port'],
									self.temp[rec]['packets'], self.temp[rec]['bytes'])
		#self.logger.info(f'elapsed {end_t - self.start_t} secs')
		self.logger.info("=" * 44)
		self.logger.info('Table 1')
		self.logger.info('datapath         '
						 'in-port  eth-dst           '
						 'out-port packets  bytes')
		self.logger.info('---------------- '
						 '-------- ----------------- '
						 '-------- -------- -------- ')
		res = sorted([flow for flow in body if flow.priority != 0 and flow.table_id == 1],
							key=lambda flow: (flow.byte_count, flow.match['in_port']),
							reverse=True) #, flow.match['eth_dst'] 
		
		if self.scan_mode == True:
			self.scan_result = res

		for stat in res:
				self.logger.info('%016x %8x %17s %8x %8d %8d',
									ev.msg.datapath.id,
									stat.match['in_port'], stat.match['eth_dst'],
									stat.instructions[0].actions[0].port,
									stat.packet_count, stat.byte_count)
		self.logger.info("=" * 44)		
		'''
		if self.Bps_rec != {}:
			for rec in self.Bps_rec:
				self.logger.info(f"{rec}: {self.Bps_rec[rec]}")
		else:
			self.logger.info('\n')
		'''
	def create_stat_record(stat_instance, in_port, eth_dst):
		return  str(stat_instance.match['in_port']) + ">" + str(stat_instance.match['eth_dst'])

	@set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
	def _port_stats_reply_handler(self, ev):

		body = ev.msg.body
		datapath = ev.msg.datapath

		self.logger.info('datapath         port     '
						 'rx-pkts  rx-bytes rx-error '
						 'tx-pkts  tx-bytes tx-error')
		self.logger.info('---------------- -------- '
						 '-------- -------- -------- '
						 '-------- -------- --------')
		for stat in sorted(body, key=attrgetter('port_no')):
				
			self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d', 
							 ev.msg.datapath.id, stat.port_no,
							 stat.rx_packets, stat.rx_bytes, stat.rx_errors,
							 stat.tx_packets, stat.tx_bytes, stat.tx_errors)

	def int_to_mac(self, macint):
		if type(macint) != int:
			raise ValueError('Invalid integer')

		return ':'.join(['{}{}'.format(a, b) for a, b in zip(*[iter('{:012x}'.format(macint))]*2)])	
	
	def mac_to_int(self, mac):
		res = re.match('^((?:(?:[0-9a-f]{2}):){5}[0-9a-f]{2})$', mac.lower())
		if res is None:
			raise ValueError('invalid mac address')
		return int(res.group(0).replace(':', ''), 16)