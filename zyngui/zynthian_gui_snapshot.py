#!/usr/bin/python3
# -*- coding: utf-8 -*-
#******************************************************************************
# ZYNTHIAN PROJECT: Zynthian GUI
# 
# Zynthian GUI Snapshot Selector (load/save)) Class
# 
# Copyright (C) 2015-2016 Fernando Moyano <jofemodo@zynthian.org>
#
#******************************************************************************
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the LICENSE.txt file.
# 
#******************************************************************************

import os
import sys
import logging
from os.path import isfile, isdir, join, basename

# Zynthian specific modules
from . import zynthian_gui_config
from . import zynthian_gui_selector

#------------------------------------------------------------------------------
# Configure logging
#------------------------------------------------------------------------------

# Set root logging level
logging.basicConfig(stream=sys.stderr, level=zynthian_gui_config.log_level)

#------------------------------------------------------------------------------
# Zynthian Load/Save Snapshot GUI Class
#------------------------------------------------------------------------------

class zynthian_gui_snapshot(zynthian_gui_selector):

	def __init__(self):
		self.base_dir=os.environ.get('ZYNTHIAN_MY_DATA_DIR',"/zynthian/zynthian-my-data") + "/snapshots"
		self.default_snapshot_fpath=join(self.base_dir,"default.zss")
		self.bank_dir=None
		self.action="LOAD"
		self.index_offset=0
		self.midi_banks={}
		self.midi_programs={}
		super().__init__('Bank', True)

	def get_snapshot_fpath(self,f):
		return join(self.base_dir,self.bank_dir,f);

	def get_next_name(self, nz=3):
		n=max(map(lambda item: int(item[2].split('-')[0]) if item[2].split('-')[0].isdigit() else 0, self.list_data))
		fmt="{0:0%dd}" % nz
		return fmt.format(n+1)

	def get_new_snapshot(self):
		return self.get_next_name(3) + '.zss'

	def get_new_bankdir(self):
		return self.get_next_name(5)

	def change_index_offset(self, i):
		self.index=self.index-self.index_offset+i
		self.index_offset=i
		if self.index<0:
			self.index=0

	def load_bank_list(self):
		self.midi_banks={}
		self.list_data=[]
		i=0
		if self.action=="SAVE" or isfile(self.default_snapshot_fpath):
			self.list_data.append((self.default_snapshot_fpath,i,"Default Snapshot"))
			i=i+1
		if self.action=="SAVE":
			self.list_data.append(("NEW_BANK",1,"New Bank"))
			i=i+1
		self.change_index_offset(i)
		for f in sorted(os.listdir(self.base_dir)):
			dpath=join(self.base_dir,f)
			if isdir(dpath):
				self.list_data.append((dpath,i,f))
				try:
					bn=self.get_midi_number(f)
					self.midi_banks[str(bn)]=i
					logging.debug("Snapshot Bank '%s' => MIDI bank %d." % (f,bn))
				except:
					logging.warning("Snapshot Bank '%s' don't have a MIDI bank number." % f)
				i=i+1

	def load_snapshot_list(self):
		self.midi_programs={}
		self.list_data=[(self.base_dir,0,"..")]
		i=1
		if self.action=="SAVE":
			self.list_data.append(("NEW_SNAPSHOT",1,"New Snapshot"))
			i=i+1
		self.change_index_offset(i)
		for f in sorted(os.listdir(join(self.base_dir,self.bank_dir))):
			fpath=self.get_snapshot_fpath(f)
			if isfile(fpath) and f[-4:].lower()=='.zss':
				#title=str.replace(f[:-4], '_', ' ')
				title=f[:-4]
				self.list_data.append((fpath,i,title))
				try:
					pn=self.get_midi_number(title)
					self.midi_programs[str(pn)]=i
					logging.debug("Snapshot '%s' => MIDI program %d." % (title,pn))
				except:
					logging.warning("Snapshot '%s' don't have a MIDI program number." % title)
				i=i+1

	def fill_list(self):
		if self.bank_dir is None:
			self.selector_caption='Bank'
			self.load_bank_list()
		else:
			self.selector_caption='Snapshot'
			self.load_snapshot_list()
		super().fill_list()

	def show(self):
		if not zynthian_gui_config.zyngui.curlayer:
			self.action=="LOAD"
		super().show()
		
	def load(self):
		self.action="LOAD"
		self.show()

	def save(self):
		self.action="SAVE"
		self.show()

	def select_action(self, i):
		try:
			fpath=self.list_data[i][0]
			fname=self.list_data[i][2]
		except:
			logging.warning("List is empty")
			return
		if fpath=='NEW_BANK':
			self.bank_dir=self.get_new_bankdir()
			os.mkdir(join(self.base_dir,self.bank_dir))
			self.show()
		elif isdir(fpath):
			if fpath==self.base_dir:
				self.bank_dir=None
				self.index=i
			else:
				self.bank_dir=self.list_data[i][2]
			self.show()
		elif self.action=="LOAD":
			if fpath=='NEW_SNAPSHOT':
				zynthian_gui_config.zyngui.screens['layer'].reset()
				zynthian_gui_config.zyngui.show_screen('layer')
			else:
				zynthian_gui_config.zyngui.screens['layer'].load_snapshot(fpath)
				#zynthian_gui_config.zyngui.show_screen('control')
		elif self.action=="SAVE":
			if fpath=='NEW_SNAPSHOT':
				fpath=self.get_snapshot_fpath(self.get_new_snapshot())
				zynthian_gui_config.zyngui.screens['layer'].save_snapshot(fpath)
				zynthian_gui_config.zyngui.show_active_screen()
			else:
				zynthian_gui_config.zyngui.show_confirm("Do you really want to overwrite the snapshot %s?" % fname, self.cb_confirm_save_snapshot,[fpath])

	def cb_confirm_save_snapshot(self, params):
		zynthian_gui_config.zyngui.screens['layer'].save_snapshot(params[0])

	def get_midi_number(self, f):
		return int(f.split('-')[0])-1

	def midi_bank_change(self, bn):
		#Get bank list if needed
		if self.bank_dir is not None:
			self.bank_dir=None
			self.fill_list()
		#Load bank dir
		bn=str(bn)
		if bn in self.midi_banks:
			self.bank_dir=self.list_data[self.midi_banks[bn]][2]
			logging.debug("Snapshot Bank Change %s: %s" % (bn,self.bank_dir))
			self.show()
			return True
		else:
			return False

	def midi_bank_change_offset(self,offset):
		old_bank_dir=self.bank_dir
		if self.bank_dir is not None:
			bn=self.get_midi_number(self.bank_dir)+offset
		else:
			bn=0
		if not self.midi_bank_change(bn):
			self.bank_dir=old_bank_dir
			self.show()

	def midi_bank_change_up(self):
		self.midi_bank_change_offset(1)
		
	def midi_bank_change_down(self):
		self.midi_bank_change_offset(-1)

	def midi_program_change(self, pn):
		#If no bank selected, default to first bank
		if self.bank_dir is None:
			self.bank_dir=self.list_data[0][2]
			self.fill_list()
		#Load snapshot
		pn=str(pn)
		if pn in self.midi_programs:
			fpath=self.list_data[self.midi_programs[pn]][0]
			logging.debug("Snapshot Program Change %s: %s" % (pn,fpath))
			zynthian_gui_config.zyngui.screens['layer'].load_snapshot(fpath)
			return True
		else:
			return False

	def midi_program_change_offset(self,offset):
		try:
			f=basename(zynthian_gui_config.zyngui.screens['layer'].last_snapshot_fpath)
			pn=self.get_midi_number(f)+offset
		except:
			pn=0
		self.midi_program_change(pn)

	def midi_program_change_up(self):
		self.midi_program_change_offset(1)
		
	def midi_program_change_down(self):
		self.midi_program_change_offset(-1)

	def next(self):
		if self.action=="SAVE": self.action="LOAD"
		elif self.action=="LOAD": self.action="SAVE"
		self.show()

	def set_select_path(self):
		title=(self.action.lower()+" snapshot").title()
		if self.bank_dir:
			title=title+": "+self.bank_dir
		self.select_path.set(title)

#------------------------------------------------------------------------------
