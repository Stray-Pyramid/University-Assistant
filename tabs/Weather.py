#Weather tab
#Updates every 10 minutes, grabbing data from darksky api
#Accuracy not guaranteed, forecasts seems to change completely after every refresh.

import os
import datetime
import time
import calendar

import requests
import json
#from bs4 import BeautifulSoup

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import *

import settings
from threads import WebFetcher
from modules import GifPlayer

wind_heading_icon = QPixmap("icons/wind_direction.png")

class Weather_Tab(QtWidgets.QFrame):
	
	auckland_latitude = -36.8485
	auckland_longitude = 174.7633
	
	update_interval = 60 * 5 #Every 5 minutes
	
	num_of_days = 5
	num_of_hours = 12
	
	hourly_icons = []
	daily_weather = []
	
	icons = {}
	
	size = QtCore.QSize(600, 300)
	hourly_weather_size = QtCore.QSize(size.width(), 60)
	current_weather_size = QtCore.QSize(260, size.height() - hourly_weather_size.height())
	daily_weather_size = QtCore.QSize(size.width() - current_weather_size.width(), 240)
	
	metservice_box_size = QtCore.QSize(60, 60)
	
	def __init__(self):
		super(Weather_Tab, self).__init__()
		
		self.load_icons()
		
		self.tabLabel = None
		
		self.thread = WebFetcher()
		self.thread.json_signal.connect(self.update_ui)
		
		duration = datetime.timedelta(minutes = 10).seconds
		self.update_timer = QtCore.QTimer(self)
		self.update_timer.timeout.connect(self.trigger_update)
		self.update_timer.start(duration * 1000)
		
	def setupUi(self, parent = None):
		
		self.setParent(parent)
		self.setGeometry(1, 1, self.size.width(), self.size.height())
		self.setObjectName("centralwidget")
		self.setStyleSheet("""*{background: #1676E6; color: white} QPushButton{border: none;}
										QFrame QLabel#current_date{font-size: 26px}
										QFrame QLabel#day_summary{font-size: 14px;}
										QFrame QLabel#current_temp{font-size: 36px;}
										QFrame QLabel#day_high{font-size: 30px; color: rgb(255, 48, 48)}
										QFrame QLabel#day_low{font-size: 30px; color: rgb(40, 227, 255)}
										QFrame QLabel#current_humdity{font-size: 24px;}
										QFrame QButton#metservice_button{margin: 5px;}
										QToolTip{color: black;}
										QPushButton#refresh_btn {background-color: none; border: none;}
		
		""")
		
		
		self.current_weather_frame = QtWidgets.QFrame(self)
		self.current_weather_frame.setGeometry(4, 2, self.current_weather_size.width(), self.current_weather_size.height())
		
		self.current_date = QtWidgets.QLabel("N/A", self.current_weather_frame)
		self.current_date.setGeometry(0,0, 200, 40)
		self.current_date.setObjectName("current_date")
		self.current_date.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		self.main_icon = QtWidgets.QLabel(self.current_weather_frame)
		self.main_icon.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
		self.main_icon.setAttribute(QtCore.Qt.WA_TranslucentBackground)
		self.main_icon.setPixmap(QPixmap("icons/weather/large/default.png").scaled(110, 110))
		self.main_icon.setGeometry(5, 40, 110, 110)
		self.main_icon.setObjectName("main_icon")
		
		shadow_effect = QtWidgets.QGraphicsDropShadowEffect()
		shadow_effect.setBlurRadius(5)
		shadow_effect.setOffset(2, 2)
		self.main_icon.setGraphicsEffect(shadow_effect)
		
		self.day_temps_frame = QtWidgets.QFrame(self.current_weather_frame)
		self.day_temps_frame.setGeometry(120, 40, 110, 110)
		self.day_temps_frame.setObjectName("day_temps_frame")
		self.day_summary = QtWidgets.QLabel("N/A", self.current_weather_frame)
		self.day_summary.setGeometry(0,150, 260, 200)
		self.day_summary.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
		self.day_summary.setWordWrap(True)
		self.day_summary.setMargin(3)
		self.day_summary.setObjectName("day_summary")
		
		#Refresh Button
		self.refresh_icon = GifPlayer("icons/ajax-loader.gif", QtCore.QPoint(self.current_weather_size.width() - 20, 0), self.current_weather_frame)
		self.refresh_icon.setCursor(QtCore.Qt.PointingHandCursor)
		self.refresh_btn = QtWidgets.QPushButton(self.refresh_icon)
		self.refresh_btn.clicked.connect(self.trigger_update)
		self.refresh_btn.setGeometry(QtCore.QRect(0, 0, 20, 20))
		self.refresh_btn.setObjectName("refresh_btn")

		self.current_temp = QtWidgets.QLabel("N/A", self.day_temps_frame)
		self.current_temp.setGeometry(0,0, 150, 40)
		self.current_temp.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		self.current_temp.setObjectName("current_temp")
		self.day_high = QtWidgets.QLabel("N/A", self.day_temps_frame)
		self.day_high.setGeometry(0,40, 75, 40)
		self.day_high.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		self.day_high.setObjectName("day_high")
		self.day_low = QtWidgets.QLabel("N/A", self.day_temps_frame)
		self.day_low.setGeometry(40,40, 150, 40)
		self.day_low.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		self.day_low.setObjectName("day_low")
		self.current_humdity = QtWidgets.QLabel("N/A", self.day_temps_frame)
		self.current_humdity.setGeometry(0,74, 150, 40)
		self.current_humdity.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		self.current_humdity.setObjectName("current_humdity")
		
		self.week_weather_frame = QtWidgets.QFrame(self)
		self.week_weather_frame.setGeometry(self.current_weather_size.width(), 0, self.daily_weather_size.width(), self.daily_weather_size.height())
		
		self.hourly_weather_frame = QtWidgets.QFrame(self)
		self.hourly_weather_frame.setGeometry(0, self.size.height() - self.hourly_weather_size.height(), self.hourly_weather_size.width(), self.hourly_weather_size.height())
		
		self.metservice_button = QtWidgets.QPushButton(QIcon("icons/metservice.png"), "", self)
		self.metservice_button.setGeometry(self.size.width() - self.metservice_box_size.width(), self.size.height() - self.metservice_box_size.height(), self.metservice_box_size.width(), self.metservice_box_size.height())
		self.metservice_button.setIconSize(QtCore.QSize(45, 45))
		self.metservice_button.setCursor(QtCore.Qt.PointingHandCursor)
		self.metservice_button.clicked.connect(self.metservice_link)
		self.metservice_button.setObjectName("metservice_button")
		
		for i in range(0, self.num_of_hours):
			hour_frame = QtWidgets.QFrame(self.hourly_weather_frame)
			hour_frame.setGeometry((i * 45), 0, 45, 60)
			
			hour_frame.hour_label = QtWidgets.QLabel("N/A", hour_frame)
			hour_frame.hour_label.setGeometry(0, 0, 45, 60)
			hour_frame.hour_label.setMargin(4)
			hour_frame.hour_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
			
			hour_frame.hour_icon = QtWidgets.QLabel(hour_frame)
			hour_frame.hour_icon.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter);
			hour_frame.hour_icon.setPixmap(QPixmap("icons/weather/small/default.png"))
			hour_frame.hour_icon.setGeometry(0, 0, 45, 50)
			hour_frame.hour_icon.setAttribute(QtCore.Qt.WA_TranslucentBackground)
			
			shadow_effect = QtWidgets.QGraphicsDropShadowEffect()
			shadow_effect.setBlurRadius(5)
			shadow_effect.setOffset(2, 2)
			hour_frame.hour_icon.setGraphicsEffect(shadow_effect)
			
			self.hourly_icons.append(hour_frame)
			
		for i in range(0, self.num_of_days):
			self.daily_weather.append(Day_Weather(self.week_weather_frame, QtCore.QSize(self.daily_weather_size.width() / self.num_of_days, self.daily_weather_size.height()), i))
		
		
		
	def trigger_update(self):
		print("Weather updating...")
		self.refresh_icon.play()
		
		try:
			self.thread.grabWebpage((settings.weather["darksky_url"] + settings.weather["darksky_api_key"] + "/" + str(self.auckland_latitude)	+ "," + str(self.auckland_longitude) + "?units=si"), output_format = "json")
		except:
			print("Weather tried to run a thread, but failed.")
		
	def update_ui(self, data):
		
	
		self.current_date.setText(datetime.datetime.fromtimestamp(data["currently"]["time"]).strftime("%x, %A"))
		self.current_temp.setText(str(round(data["currently"]["temperature"])) + u"\u00b0" + "C")
		self.day_high.setText(str(round(data["daily"]["data"][0]["temperatureHigh"])))
		self.day_low.setText(str(round(data["daily"]["data"][0]["temperatureLow"])))
		self.current_humdity.setText(str(int(data["daily"]["data"][0]["humidity"] * 100)) + "%")
		self.day_summary.setText(data["daily"]["summary"])

		
		print("Current weather is " + data["currently"]["icon"])
		self.main_icon.setPixmap(self.icons["large"][data["currently"]["icon"]].scaled(110, 110))
		
		for i in range(0, self.num_of_days):
			day_data = data["daily"]["data"][i + 1]
			self.daily_weather[i].update(datetime.datetime.fromtimestamp(day_data["time"]), self.icons["normal"][day_data["icon"]], day_data["windSpeed"], day_data["windBearing"], day_data["temperatureHigh"], day_data["temperatureLow"])
			#(self, datetime, icon, windSpeed, windDirection, temp_high, temp_low)
			
		for i in range(0, self.num_of_hours):
			#print("%s: %s" % (i, data["hourly"]["data"][i]["icon"]))
			self.hourly_icons[i].hour_icon.setPixmap(self.icons["small"][data["hourly"]["data"][i]["icon"]])
			self.hourly_icons[i].hour_label.setText(datetime.datetime.fromtimestamp(data["hourly"]["data"][i]["time"]).strftime("%I%p"))
		
		self.refresh_btn.setToolTip("Last updated " + datetime.datetime.now().strftime("%X %x"))
		
		self.refresh_icon.reset()
		print("Weather updated.")
		
	def metservice_link(self):

		QDesktopServices.openUrl(QtCore.QUrl(settings.weather["metservice_auckland_url"]))
		
	
	def load_icons(self):
		icons_dir = "icons\\weather"
		
		small_icons = {}
		small_icons_dir = os.path.join(os.getcwd(), icons_dir, "small")
		small_icons_files = os.listdir(small_icons_dir)
		for small_icon in small_icons_files:
			if small_icon[-3:] == "png":
				small_icons[small_icon[:-4]] = QPixmap(os.path.join(small_icons_dir, small_icon))
			
		normal_icons = {}
		normal_icons_dir = os.path.join(os.getcwd(), icons_dir, "normal")
		normal_icons_files = os.listdir(normal_icons_dir)
		for normal_icon in normal_icons_files:
			if normal_icon[-3:] == "png":
				normal_icons[normal_icon[:-4]] = QPixmap(os.path.join(normal_icons_dir, normal_icon))
				
		large_icons = {}
		large_icons_dir = os.path.join(os.getcwd(), icons_dir, "large")
		large_icons_files = os.listdir(large_icons_dir)
		for large_icon in large_icons_files:
			if large_icon[-3:] == "png":
				large_icons[large_icon[:-4]] = QPixmap(os.path.join(large_icons_dir, large_icon))
		
		
		#Add icons to object...
		self.icons["small"] = small_icons
		self.icons["normal"] = normal_icons
		self.icons["large"] = large_icons
		
		
class Day_Weather(QtWidgets.QFrame):
	
	def __init__(self, parent, size, index):
		super(Day_Weather, self).__init__()
		self.setParent(parent)
		self.setGeometry((size.width() * index), 0, size.width(), size.height())
		
		self.setStyleSheet("""QFrame QLabel#day_name{background: #004AF3; font-size: 24px;}
									   QFrame QLabel#temp_high_label{background: #ED1C24; font-size: 16px;}
									   QFrame QLabel#temp_low_label{background: #0054A6; font-size: 16px;}
									   QFrame QLabel#wind_speed_label{font-size: 16px; color: black;}
									""")
			
		self.day_label = QtWidgets.QLabel("N/A", self)
		self.day_label.setGeometry(0, 0, size.width(), 30)
		self.day_label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)	
		self.day_label.setObjectName("day_name")
		
		self.weather_icon = QtWidgets.QLabel(self)
		self.weather_icon.setPixmap(QPixmap("icons/weather/small/default.png"))
		self.weather_icon.setAttribute(QtCore.Qt.WA_TranslucentBackground)
		self.weather_icon.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
		self.weather_icon.setGeometry(0, 30, size.width(), 90)
		
		shadow_effect = QtWidgets.QGraphicsDropShadowEffect()
		shadow_effect.setBlurRadius(5)
		shadow_effect.setOffset(2, 2)
		self.weather_icon.setGraphicsEffect(shadow_effect)
		
		self.wind_speed_background = QtWidgets.QLabel(self)
		self.wind_speed_background.setPixmap(QPixmap("icons/wind_circle.png"))
		self.wind_speed_background.setGeometry(0, 120, size.width(), size.width())
		self.wind_speed_background.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
		self.wind_speed_background.setAttribute(QtCore.Qt.WA_TranslucentBackground)
		
		self.wind_speed = QtWidgets.QLabel("N/A", self)
		self.wind_speed.setGeometry(0, 120, size.width(), size.width())
		self.wind_speed.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
		self.wind_speed.setAttribute(QtCore.Qt.WA_TranslucentBackground)
		self.wind_speed.setObjectName("wind_speed_label")
		
		self.wind_direction = QtWidgets.QLabel(self)
		self.wind_direction.setPixmap(wind_heading_icon)
		self.wind_direction.setGeometry(0, 120, size.width(), size.width())
		self.wind_direction.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
		self.wind_direction.setAttribute(QtCore.Qt.WA_TranslucentBackground)
		
		self.temp_high_label = QtWidgets.QLabel("N/A", self)
		self.temp_high_label.setGeometry(0, size.height() - 48, size.width(), 24)
		self.temp_high_label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
		self.temp_high_label.setObjectName("temp_high_label")
		
		self.temp_low_label = QtWidgets.QLabel("N/A", self)
		self.temp_low_label.setGeometry(0, size.height() - 24, size.width(), 24)
		self.temp_low_label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
		self.temp_low_label.setObjectName("temp_low_label")
		
		
	def update(self, datetime, icon, windSpeed, windDirection, temp_high, temp_low):
				
		self.day_label.setText(datetime.strftime("%a"))
		self.weather_icon.setPixmap(icon)
		self.wind_speed.setText(str(round(windSpeed)))
		self.temp_high_label.setText(str(round(temp_high)) + u"\u00b0")
		self.temp_low_label.setText(str(round(temp_low)) + u"\u00b0")
		
		#Rotate the wind direction arrow around its circle
		transform_tool = QTransform()
		transform_tool.rotate(windDirection)
		wind_direction_arrow = QPixmap(wind_heading_icon.transformed(transform_tool, QtCore.Qt.SmoothTransformation))
		self.wind_direction.setPixmap(wind_direction_arrow)