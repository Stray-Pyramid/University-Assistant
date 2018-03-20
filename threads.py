from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import *

import requests
from bs4 import BeautifulSoup
import json

import psycopg2 as PostgreDB

import settings

class WebFetcher(QtCore.QThread):
	
	html_signal = QtCore.pyqtSignal(BeautifulSoup)
	json_signal = QtCore.pyqtSignal(dict)
	
	def __init__(self, header = None, parent=None):
		super(WebFetcher, self).__init__(parent)
		
		self.mutex = QtCore.QMutex()
		
	def grabWebpage(self, url, header = None, output_format = "html"):
		locker = QtCore.QMutexLocker(self.mutex)
		
		self.url = url
		self.header = header
		self.output_format = output_format
		
		if not self.isRunning():
			self.start(QtCore.QThread.LowPriority)


	def run(self):
		
		self.mutex.lock()
		url = self.url
		header = self.header
		data = None
		output_format = self.output_format
		self.mutex.unlock()
		
		try:
			response = requests.get(url, headers = header)
			if output_format == "html":
				data = BeautifulSoup(response.content, "html.parser")	
				self.html_signal.emit(data)
			elif output_format == "json":
				data = json.loads(response.text)
				self.json_signal.emit(data)
			else:
				self.html_signal.emit(data)
		except:
			print("WebFetcher thread failed.")
		

class DatabaseFetcher(QtCore.QThread):
	
	data_ready = QtCore.pyqtSignal(str, list, str)
	
	def __init__(self, header = None, parent=None):
		super(DatabaseFetcher, self).__init__(parent)
		
		self.mutex = QtCore.QMutex()
		self.queue = []

	def execute(self, query_data):
		try:
			locker = QtCore.QMutexLocker(self.mutex)
			
			self.query_scaffold = query_data[0]
			self.query_data = query_data[1]
			self.reference = query_data[2]
			
			if not self.isRunning():
				self.start(QtCore.QThread.LowPriority)
		except:
			print("DBFetcher: sendQuery failed to execute.")
		
	
	def run(self):
		
		data = []
		result = "success"
		
		try:
			self.mutex.lock()
			query_scaffold = self.query_scaffold.strip()
			query_data = self.query_data
			reference = self.reference
			self.mutex.unlock()
			
			db = PostgreDB.connect(**settings.postgresql_settings)
			cur = db.cursor()
			
			#TODO: retry if timeout
			cur.execute(query_scaffold, query_data)
			
			query_type = query_scaffold[:6]
			if query_type == "select":
				data = cur.fetchall()
			elif query_type == "insert":
				data = cur.fetchone()
			
			db.commit()
			cur.close()
			db.close()
			
		except PostgreDB.DatabaseError as e:
			print(e)
			result = "failure"
			
		finally:
			self.data_ready.emit(result, data, reference)