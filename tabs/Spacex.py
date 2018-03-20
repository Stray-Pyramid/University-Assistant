#disabled because of manifest problems

import datetime
import time
import calendar
import math

import MySQLdb
import requests
from bs4 import BeautifulSoup

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import *

import settings
from threads import WebFetcher
from modules import GifPlayer

launch_schedule_url = "https://www.reddit.com/r/SpaceX/wiki/launches/manifest"
spacex_webcast_url = "http://www.spacex.com/webcast"

column_width_1 = 97
column_width_2 = 76
column_width_3 = 190

timer_override = False
time_override_value = "2018-02-23 17:05:30"

update_interval = datetime.timedelta(hours = 24)

class Spacex_Tab(QtWidgets.QFrame):
	size = QtCore.QSize(364, 422)
	
	def __init__(self):
		super(Spacex_Tab, self).__init__()
		
		self.updating = False
		self.thread = WebFetcher()
		self.thread.html_signal.connect(self.update_ui)
		
		self.table_rows = []
		
		self.countdown_time = None
		self.countdown_timer = QtCore.QTimer(self)
		self.countdown_timer.timeout.connect(self.update_countdown)
		self.countdown_timer.start(1000)
		
		self.last_update_time = None
		
		self.tabLabel = None

	def setupUi(self, parent = None):
		self.setGeometry(1,1, self.size.width(), self.size.height())
		
		
		
		#Main container
		self.setParent(parent)
		self.setObjectName("centralwidget")
		self.setStyleSheet("""#centralwidget{background: red}
							QPushButton#refresh_btn {background-color: none; border: none;}
							""")
		
		
		#Launch Schedule countdown
		self.countdown_frame = QtWidgets.QFrame(self)
		self.countdown_frame.setGeometry(0, 0, self.size.width(), 122)
		self.countdown_frame.setObjectName("countdown_frame")
		self.countdown_frame.setStyleSheet("""QFrame{background-color: rgb(35, 35, 35); color: white}
											QFrame#t{font-size: 20px; background: none}
											QFrame#number{font-size: 48px; background: none}
											QFrame#title{font-size: 10px}
											QFrame#under_text{font-size: 20px}
											QFrame#countdown_frame QFrame QPushButton{color: white; background-color: rgb(244, 66, 54); border-radius: 2px; padding: 5px;}
											""")
		
		
		
		
		#Days
		self.days_num_label = QtWidgets.QLabel("0", self.countdown_frame)
		self.days_label = QtWidgets.QLabel("DAYS", self.countdown_frame)
		self.days_num_label.setGeometry(0,0, self.size.width() / 4, 64)
		self.days_label.setGeometry(0, 64, self.size.width() / 4, 14)
		self.days_num_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
		self.days_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
		self.days_num_label.setObjectName("number")
		self.days_label.setObjectName("title")
		
		#Hours
		self.hours_num_label = QtWidgets.QLabel("0", self.countdown_frame)
		self.hours_label = QtWidgets.QLabel("HOURS", self.countdown_frame)
		self.hours_num_label.setGeometry(self.size.width() / 4, 0, self.size.width() / 4, 64)
		self.hours_label.setGeometry(self.size.width() / 4, 64, self.size.width() / 4, 14)
		self.hours_num_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
		self.hours_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
		self.hours_num_label.setObjectName("number")
		self.hours_label.setObjectName("title")
		
		#Minutes
		self.minutes_num_label = QtWidgets.QLabel("0", self.countdown_frame)
		self.minutes_label = QtWidgets.QLabel("MINUTES", self.countdown_frame)
		self.minutes_num_label.setGeometry((self.size.width() / 4) * 2, 0, self.size.width() / 4, 64)
		self.minutes_label.setGeometry((self.size.width() / 4) * 2, 64, self.size.width() / 4, 14)
		self.minutes_num_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
		self.minutes_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
		self.minutes_num_label.setObjectName("number")
		self.minutes_label.setObjectName("title")
		
		#Seconds
		self.seconds_num_label = QtWidgets.QLabel("0", self.countdown_frame)
		self.seconds_label = QtWidgets.QLabel("SECONDS", self.countdown_frame)
		self.seconds_num_label.setGeometry((self.size.width() / 4) * 3, 0, self.size.width() / 4, 64)
		self.seconds_label.setGeometry((self.size.width() / 4) * 3, 64, self.size.width() / 4, 14)
		self.seconds_num_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
		self.seconds_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
		self.seconds_num_label.setObjectName("number")
		self.seconds_label.setObjectName("title")
		
		#T-, T+
		self.t_label = QtWidgets.QLabel("T-", self.countdown_frame)
		self.t_label.setGeometry(0,0, 30, 78)
		self.t_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
		self.t_label.setObjectName("t")
		
		#Under text
		self.lower_box = QtWidgets.QFrame(self.countdown_frame)
		self.lower_box.setGeometry(QtCore.QRect(0, 78, self.size.width(), 42))
		
		self.horizontalLayout = QtWidgets.QHBoxLayout(self.lower_box)
		self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
		self.horizontalLayout.setObjectName("horizontalLayout")
		
		#////
		leftSpacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.horizontalLayout.addItem(leftSpacer)
		
		self.lower_box.label = QtWidgets.QLabel("Connecting to server...", self.lower_box)
		self.lower_box.label.setStyleSheet("*{font-size: 20px}")
		self.horizontalLayout.addWidget(self.lower_box.label)
		
		self.lower_box.stream_link_button = QtWidgets.QPushButton("OPEN STREAM", self.lower_box)
		self.lower_box.stream_link_button.setStyleSheet("*{font-size: 16px}")
		self.lower_box.stream_link_button.setCursor(QtCore.Qt.PointingHandCursor)
		self.lower_box.stream_link_button.clicked.connect(self.openSpaceStream)
		self.lower_box.stream_link_button.hide()
		self.horizontalLayout.addWidget(self.lower_box.stream_link_button)
		
		rightSpacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.horizontalLayout.addItem(rightSpacer)
		#////
		
		#Launch Schedule Table
		self.launch_schedule_table = QtWidgets.QFrame(self)
		self.launch_schedule_table.setGeometry(0, 122, self.size.width(), 301)
		
		self.launch_schedule_header = QtWidgets.QFrame(self.launch_schedule_table)
		self.launch_schedule_header.setGeometry(0, 0, self.size.width(), 20)
		self.launch_schedule_header.setStyleSheet("""QFrame{background-color: rgb(86, 86, 86)}
																			QLabel{font-size: 10px; border-left: 1px solid white; color: white; padding-left: 3px}""")
		
		self.launchDate_label = QtWidgets.QLabel("Launch Date", self.launch_schedule_header)
		self.launchDate_label.setGeometry(-1, 2, column_width_1, 16)
		self.vehicle_label = QtWidgets.QLabel("Vehicle", self.launch_schedule_header)
		self.vehicle_label.setGeometry(column_width_1, 2, column_width_2, 16)
		self.payload_label = QtWidgets.QLabel("Payload", self.launch_schedule_header)
		self.payload_label.setGeometry(column_width_1 + column_width_2, 2, column_width_3, 16)
		
		
		for x in range(0, 7):
			self.table_rows.append(QtWidgets.QFrame(self.launch_schedule_table))
			self.table_rows[x].setGeometry(0, 20 + (x * 40), self.size.width(), 40)
			
			self.table_rows[x].launch_date_label = QtWidgets.QLabel("", self.table_rows[x])
			self.table_rows[x].launch_date_label.setGeometry(0,0, column_width_1, 40)
			self.table_rows[x].launch_date_label.setWordWrap(True)
			self.table_rows[x].launch_vehicle_label = QtWidgets.QLabel("", self.table_rows[x])
			self.table_rows[x].launch_vehicle_label.setGeometry(column_width_1,0, column_width_2, 40)
			self.table_rows[x].launch_vehicle_label.setWordWrap(True)
			self.table_rows[x].launch_payload_label = QtWidgets.QLabel("", self.table_rows[x])
			self.table_rows[x].launch_payload_label.setGeometry(column_width_1 + column_width_2,0, column_width_3, 40)
			self.table_rows[x].launch_payload_label.setWordWrap(True)
			
			if x % 2 == 1:
				self.table_rows[x].setStyleSheet("QFrame{background-color: rgb(255, 255, 255); font-size: 9px; padding-left: 4px}")
			else:
				self.table_rows[x].setStyleSheet("QFrame{background-color: rgb(247, 247, 247); font-size: 9px; padding-left: 4px}")
		
		#Refresh Button
		self.refresh_icon = GifPlayer("icons/ajax-loader.gif", QtCore.QPoint(0, 0), self)
		self.refresh_icon.setCursor(QtCore.Qt.PointingHandCursor)
		self.refresh_btn = QtWidgets.QPushButton(self.refresh_icon)
		self.refresh_btn.clicked.connect(self.trigger_update)
		self.refresh_btn.setGeometry(QtCore.QRect(0, 0, 20, 20))
		self.refresh_btn.setObjectName("refresh_btn")
		
		

	def trigger_update(self):
		print("Spacex updating...")
	
		self.refresh_icon.play()
	
		if self.updating == False:
			self.updating = True
			try:
				self.thread.grabWebpage(launch_schedule_url, header ={'User-agent': 'SpaceX Timetable Scraper V1'})
			except:
				print("Spacex tried to run a thread, but failed.")
	
	def update_ui(self, webpage_content):
		#Get launch schedule table
		launch_schedule_table = webpage_content.find('div', attrs={"class": "wiki"}).findAll("table")[0].contents[1]
		
		for x in range(0, 7):

			launch = launch_schedule_table.contents[5 + (x * 2)]
			launch_date = launch.contents[1].text
			launch_vehicle = launch.contents[3].text.replace("\u267a", "R")
			launch_payload = launch.contents[11].text
						
			self.table_rows[x].launch_date_label.setText(launch_date)
			self.table_rows[x].launch_vehicle_label.setText(launch_vehicle)
			self.table_rows[x].launch_payload_label.setText(launch_payload)
		
		self.update_countdown_time()
		
		self.last_update_time = datetime.datetime.now()
		
		# This is most definitely unnecessary.
		del launch_schedule_table
		
		self.refresh_icon.reset()
		self.updating = False
		print("SpaceX module updated.")
	
	def interpret_time(self, time_to_interpret):
		try:
			if len(time_to_interpret.split(" ")) == 4:
				return datetime.datetime.strptime(time_to_interpret, "%Y %b %d [%H:%M]")
			else:
				return datetime.datetime.strptime(time_to_interpret, "%Y %b %d")
		except:
			return None
	
	def update_countdown_time(self):
		if not timer_override:
			self.countdown_time = self.interpret_time(self.table_rows[0].launch_date_label.text())
			if self.countdown_time != None:
				if ((self.countdown_time + datetime.timedelta(hours = 13)) - datetime.datetime.now()) < datetime.timedelta(minutes = -5):
					self.countdown_time = self.interpret_time(self.table_rows[1].launch_date_label.text())
		else:
			self.countdown_time = datetime.datetime.strptime(time_override_value, "%Y-%m-%d %H:%M:%S") - datetime.timedelta(hours = 13)
	
	def update_countdown(self):
		if self.countdown_time != None:
			if self.last_update_time + update_interval < datetime.datetime.now():
				self.trigger_update()
		
			time_left = (self.countdown_time + datetime.timedelta(hours = 13)) - datetime.datetime.now()
			
			if time_left < datetime.timedelta(minutes = -5) and timer_override != True:
				self.update_countdown_time()
				self.lower_box.label.setText("TILL NEXT LAUNCH")
				self.lower_box.stream_link_button.hide()
				self.tabLabel.changeState(settings.tabLabel_status.NORMAL)
			elif time_left < datetime.timedelta(minutes = 5) and time_left > datetime.timedelta(minutes = -5):
				self.lower_box.label.setText("LAUNCHING NOW")
				self.lower_box.stream_link_button.show()
				self.tabLabel.changeState(settings.tabLabel_status.ALERT)
			elif time_left < datetime.timedelta(minutes = 60):
				self.lower_box.label.setText("LAUNCHING SOON")
				self.lower_box.stream_link_button.show()
				self.tabLabel.changeState(settings.tabLabel_status.NOTICE)
			else:
				self.lower_box.label.setText("TILL NEXT LAUNCH")
				self.lower_box.stream_link_button.hide()
				self.tabLabel.changeState(settings.tabLabel_status.NORMAL)
				
			if time_left.seconds > 0:
				self.t_label.setText("T-")
			else:
				self.t_label.setText("T+")
			
			
			
			days = int(time_left.total_seconds() / 86400)
			hours = int(time_left.total_seconds() / 3600) - (days * 24)
			minutes = int(time_left.total_seconds() / 60) - ((hours * 60) + (days * 1440))
			seconds = int(time_left.total_seconds()) - ((minutes * 60) + (hours * 3600) + (days * 86400))
			
			self.days_num_label.setText(str(abs(days)))
			self.hours_num_label.setText(str(abs(hours)))
			self.minutes_num_label.setText(str(abs(minutes)))
			self.seconds_num_label.setText(str(abs(seconds)))
			
		else:
			self.lower_box.label.setText("Invalid Time")
			
			
			
	def openSpaceStream(self):
		QDesktopServices.openUrl(QtCore.QUrl(spacex_webcast_url))