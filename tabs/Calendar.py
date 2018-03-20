import os, sys
import datetime
import time
import calendar

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import *

from threads import DatabaseFetcher
from modules import GifPlayer

class Calendar_Tab(QtWidgets.QWidget):
	
	size = QtCore.QSize(700, 700)
	cells = []
	
	def __init__(self):
		super(Calendar_Tab, self).__init__()

		self.active_date = datetime.datetime.today().replace(day=1)

		self.inputWidget = Calendar_Form()
		self.inputWidget.submit_data.connect(self.trigger_cell_update)
				
		self.updating = False
		self.thread = DatabaseFetcher()
		self.thread.data_ready.connect(self.update_calendar_cells)
		
		self.tabLabel = None
		self.queryQueue = []
		
		#Update every hour
		seconds_in_hour = datetime.timedelta(hours = 1).seconds
		self.update_timer = QtCore.QTimer(self)
		self.update_timer.timeout.connect(self.trigger_update)
		self.update_timer.start(seconds_in_hour * 1000)
		
	def setupUi(self, parent = None):
		self.setGeometry(1,1, self.size.width(), self.size.height())
		
		self.setParent(parent)
		self.setObjectName("centralwidget")
		self.setStyleSheet("""
														#centralwidget QFrame QFrame{color: white; font-family:'Arial'; padding: 0px 0px 2px 0px;} 
														QWidget QFrame QLabel#day_number{background-color: rgb(100, 100, 100); font-size: 12px; font-weight: bold;} 
														QWidget QFrame QLabel#contents{background-color: rgb(140, 140, 140); font-size: 9px; margin: -1px;}
														QPushButton {background-color: none; border: none;}
														QPushButton#minimize:hover {background-color: rgb(110, 110, 110);}
														QPushButton#quit:hover {background-color: rgb(215, 0, 0);}
													""")
													
		self.gridLayoutWidget = QtWidgets.QWidget(self)
		self.gridLayoutWidget.setGeometry(QtCore.QRect(0, 100, 700, 600))
		self.gridLayoutWidget.setObjectName("gridLayoutWidget")
		self.gridLayoutWidget.setStyleSheet("QWidget#gridLayoutWidget{background-color: rgb(160, 160, 160)}")
		self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
		self.gridLayout.setContentsMargins(0, 0, 0, 0)
		self.gridLayout.setSpacing(1)
		self.gridLayout.setObjectName("gridLayout")
		
		self.title_frame = QtWidgets.QFrame(self)
		self.title_frame.setGeometry(QtCore.QRect(0, 0, 700, 100))
		self.title_frame.setObjectName("title_frame")
		self.title_frame.setStyleSheet("#title_frame{background-color: rgb(100, 100, 100); border-bottom: 1px solid rgb(160, 160, 160)} QLabel {color: rgb(190, 190, 190); font-size: 20px;}")
		#Main Date Title
		self.label = QtWidgets.QLabel(self.title_frame)
		self.label.setGeometry(QtCore.QRect(215, -2, 200, 80))
		self.label.setTextFormat(QtCore.Qt.AutoText)
		self.label.setScaledContents(False)
		self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTop)
		self.label.setObjectName("date")
		
		#<-, ->, New reminder, refresh buttons
		self.month_past = QtWidgets.QPushButton(QIcon("icons/arrow_left.png"), "", self.title_frame)
		self.month_past.setObjectName("btn_previous_month")
		self.month_past.clicked.connect(self.previous_month)
		self.month_past.setGeometry(QtCore.QRect(416, 4, 20, 20))
		self.month_past.setCursor(QtCore.Qt.PointingHandCursor)
		
		self.month_future = QtWidgets.QPushButton(QIcon("icons/arrow_right.png"), "", self.title_frame)
		self.month_future.setObjectName("btn_next_month")
		self.month_future.clicked.connect(self.next_month)
		self.month_future.setGeometry(QtCore.QRect(436, 4, 20, 20))
		self.month_future.setCursor(QtCore.Qt.PointingHandCursor)
		
		self.new_reminder = QtWidgets.QPushButton(QIcon("icons/pencil.png"), "", self.title_frame)
		self.new_reminder.setObjectName("btn_new_reminder")
		self.new_reminder.clicked.connect(self.new_blank_reminder)
		self.new_reminder.setGeometry(QtCore.QRect(456, 4, 20, 20))
		self.new_reminder.setCursor(QtCore.Qt.PointingHandCursor)
		
		#Refresh Button
		self.refresh_icon = GifPlayer("icons/ajax-loader.gif", QtCore.QPoint(476, 7), self.title_frame)
		self.refresh_icon.setCursor(QtCore.Qt.PointingHandCursor)
		self.refresh_btn = QtWidgets.QPushButton(self.refresh_icon)
		self.refresh_btn.clicked.connect(self.trigger_update)
		self.refresh_btn.setGeometry(QtCore.QRect(0, 0, 20, 20))
		self.refresh_btn.setObjectName("refresh_btn")
		
		#Day Labels
		self.days = QtWidgets.QFrame(self.title_frame)
		self.days.setGeometry(QtCore.QRect(1, 79, 700, 20))
		self.days.setStyleSheet("#days QLabel{color: rgb(190, 190, 190);font-size: 15px;}")
		#rgb(100, 100, 100)
		self.days.setFrameShape(QtWidgets.QFrame.StyledPanel)
		self.days.setFrameShadow(QtWidgets.QFrame.Raised)
		self.days.setObjectName("days")
       
		self.label_sun = QtWidgets.QLabel("Sun", self.days)
		self.label_sun.setGeometry(QtCore.QRect(0, 0, 100, 20))
		self.label_sun.setAlignment(QtCore.Qt.AlignHCenter)
		self.label_sun.setObjectName("label_sun")
		self.label_mon = QtWidgets.QLabel("Mon", self.days)
		self.label_mon.setGeometry(QtCore.QRect(100, 0, 100, 20))
		self.label_mon.setAlignment(QtCore.Qt.AlignHCenter)
		self.label_mon.setObjectName("label_mon")
		self.label_tue = QtWidgets.QLabel("Tue", self.days)
		self.label_tue.setGeometry(QtCore.QRect(200, 0, 100, 20))
		self.label_tue.setAlignment(QtCore.Qt.AlignHCenter)
		self.label_tue.setObjectName("label_tue")
		self.label_wed = QtWidgets.QLabel("Wed", self.days)
		self.label_wed.setGeometry(QtCore.QRect(300, 0, 100, 20))
		self.label_wed.setAlignment(QtCore.Qt.AlignHCenter)
		self.label_wed.setObjectName("label_wed")
		self.label_thu = QtWidgets.QLabel("Thu", self.days)
		self.label_thu.setGeometry(QtCore.QRect(400, 0, 100, 20))
		self.label_thu.setAlignment(QtCore.Qt.AlignHCenter)
		self.label_thu.setObjectName("label_thu")
		self.label_fri = QtWidgets.QLabel("Fri", self.days)
		self.label_fri.setGeometry(QtCore.QRect(500, 0, 100, 20))
		self.label_fri.setAlignment(QtCore.Qt.AlignHCenter)
		self.label_fri.setObjectName("label_fri")
		self.label_sat = QtWidgets.QLabel("Sat", self.days)
		self.label_sat.setGeometry(QtCore.QRect(600, 0, 100, 20))
		self.label_sat.setAlignment(QtCore.Qt.AlignHCenter)
				
		self.populate_cells()
		QtCore.QMetaObject.connectSlotsByName(self)
				
	def populate_cells(self):
		
		for y in range(0, 6):
			for x in range(0, 7):
				cell = Calendar_Cell(self.gridLayoutWidget, self.inputWidget)
				self.gridLayout.addWidget(cell, y, x, 1, 1)
				self.cells.append(cell)
		
	
	def trigger_update(self):
		if self.updating:
			return
		
		print("Calender updating...")
		self.updating = True
		self.update_calendar_dates()
		
		cell_contents_query = """SELECT date, contents FROM "Schema"."Table" 
								 WHERE DATE_PART('year', timestamp %s) <= date_part('year', date) AND DATE_PART('doy', TIMESTAMP %s) <= DATE_PART('doy', date) 
								 AND DATE_PART('year', timestamp %s) >= date_part('year', date) AND DATE_PART('doy', TIMESTAMP %s) >= DATE_PART('doy', date);"""
		
		start_date = self.cells[0].date.strftime("%Y-%m-%d")
		end_date = self.cells[-1].date.strftime("%Y-%m-%d")
				
		self.queryQueue.append([cell_contents_query, (start_date, start_date, end_date, end_date), "select"])
		self.runQueue()

			
	def update_calendar_cells(self, result, data, reference):
		
		if result == "success":
			for cell_data in data:
				days_delta = (cell_data[0] - self.cells[0].date).days + 1
				
				if days_delta < 0 or days_delta > 41:
					continue
				
				self.cells[days_delta].content.setText(cell_data[1])
				self.cells[days_delta].refresh_gif.hide()
				self.cells[days_delta].content.show()
				
			self.refresh_btn.setToolTip("Last updated " + datetime.datetime.now().strftime("%X %x"))
			print("Calendar updated.")
			
		else:
			print("Calendar failed to update.")
		
		self.refresh_icon.reset()
		self.updating = False

		
	def update_calendar_dates(self):
				
		self.refresh_icon.play()
		
		current_month = calendar.monthrange(self.active_date.year, self.active_date.month)
		#(first day, number of days in month)
		month_start = current_month[0] + 1
		
		self.label.setText(self.active_date.strftime("%B, %Y"))
		
		
		for column in range(0, 6):
			for row in range(0, 7):
				
				cell_num = row + (column * 7)
				active_cell = self.cells[cell_num]
				
				if cell_num < month_start:
					active_cell.date = (self.active_date - datetime.timedelta(days=(month_start - cell_num)))
				else:
					active_cell.date = (self.active_date + datetime.timedelta(days=(cell_num - month_start)))
				
				#Default
				active_cell.dayNum.setText(active_cell.date.strftime("%d").lstrip('0'))

				#current day: red
				#Sunday: light red
				#Saturday: light blue
				#current month: white
				#other month: light green
				
				if active_cell.date.date() == datetime.date.today():
					active_cell.setStyleSheet("#day_number{color: rgb(220, 20, 20)}")
				elif active_cell.date.month != self.active_date.month:
					active_cell.setStyleSheet("#day_number{color: rgb(115, 150, 115)}")
				elif active_cell.date.weekday() == 5:
					active_cell.setStyleSheet("#day_number{color: rgb(125, 125, 190)}")
				elif active_cell.date.weekday() == 6:
					active_cell.setStyleSheet("#day_number{color: rgb(190, 125, 125)}")
				else:
					active_cell.setStyleSheet("#day_number{color: white}")
		
	
	def previous_month(self):
		self.change_month(-1)
		
	def next_month(self):
		self.change_month(1)
		
	def change_month(self, delta_month):
		
		if delta_month < 0:
			month = self.active_date.month - 1
			year = self.active_date.year 
			if month == 0:
				year -= 1
				month = 12
		
			day_difference = calendar.monthrange(year, month)[1]
			self.active_date = self.active_date - datetime.timedelta(days = day_difference)
		else:
			day_difference = calendar.monthrange(self.active_date.year, self.active_date.month)[1]
			self.active_date = self.active_date + datetime.timedelta(days = day_difference)
		
		self.clear_calendar_cells()
		self.trigger_update()
		
	def clear_calendar_cells(self):
		for column in range(0, 6):
			for row in range(0, 7):
				cell_num = row + (column * 7)
				self.cells[cell_num].content.setText("")
		
	def new_blank_reminder(self):
		self.inputWidget.editCell(self.active_date)
	
	def trigger_cell_update(self, date, content):
		current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		self.thread.addToQueue(""" SELECT date, contents FROM Calendar_Insert(%s, %s, %s) """, (date, current_datetime, content), mode = "select")
		self.thread.execute()
		
		#Cycle through calendar cells, is there a cell matching the one being edited?
		for column in range(0, 6):
			for row in range(0, 7):
				cell = self.cells[row + (column*7)]
				if cell.date.strftime("%Y-%m-%d") == date:
					
					cell.refresh_gif.show()
					cell.refresh_gif.play()
					cell.content.hide()
					
					return
			
	def runQueue(self):
		if(len(self.queryQueue) > 0):

			if(self.thread.isRunning() == False):
				self.thread.execute(self.queryQueue[0])
				self.refresh_icon.play()
				self.updating = True
		
		else:
			self.refresh_icon.reset()
			self.updating = False
				
class Calendar_Cell(QtWidgets.QFrame):
	
	def __init__(self, parent, calendarInputWidget):
		super(Calendar_Cell, self).__init__()
		
		self.date = None
		self.inputWidget = calendarInputWidget
		
		#Cell container
		self.setParent(parent)
		self.setFrameShape(QtWidgets.QFrame.StyledPanel)
		self.setFrameShadow(QtWidgets.QFrame.Raised)
		self.setObjectName("day_container")
		self.setCursor(QtCore.Qt.PointingHandCursor)
		
		#Day number
		self.dayNum = QtWidgets.QLabel(self)
		self.dayNum.setGeometry(QtCore.QRect(0, 0, 100, 15))
		self.dayNum.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
		self.dayNum.setObjectName("day_number")
		
		#Contents
		self.content = QtWidgets.QLabel(self)
		self.content.setGeometry(QtCore.QRect(0, 15, 100, 85))
		self.content.setFrameShape(QtWidgets.QFrame.NoFrame)
		self.content.setLineWidth(0)
		self.content.setScaledContents(False)
		self.content.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
		self.content.setObjectName("contents")
		self.content.setWordWrap(True);
		
		self.refresh_gif = GifPlayer("icons/loading.gif", QtCore.QPoint(7.5, 17.5), self)
		self.refresh_gif.hide()
		
	def mouseDoubleClickEvent(self, e):
		self.inputWidget.editCell(self.date, self.content.text())

class Calendar_Form(QtWidgets.QWidget):
		
	
	submit_data = QtCore.pyqtSignal(str, str)
	
	def __init__(self):
		super(Calendar_Form, self).__init__()
		self.setup_ui()
		
	def setup_ui(self):
		self.setObjectName("Form")
		self.setWindowTitle("Form")
		self.resize(320, 390)
		self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
		
		self.calendar = QtWidgets.QCalendarWidget(self)
		self.calendar.setGeometry(QtCore.QRect(10, 200, 261, 183))
		self.calendar.setObjectName("calendarWidget")
		
		self.text_box = QtWidgets.QPlainTextEdit(self)
		self.text_box.setGeometry(QtCore.QRect(10, 10, 261, 181))
		self.text_box.setObjectName("plainTextEdit")
		
		self.submit_button = QtWidgets.QPushButton(QIcon("icons/tick.png"), "", self)
		self.submit_button.setGeometry(QtCore.QRect(280, 10, 30, 30))
		self.submit_button.clicked.connect(self.submit)
		self.submit_button.setIconSize(QtCore.QSize(30, 30))
		self.submit_button.setObjectName("submit")
		
		self.cancel_button = QtWidgets.QPushButton(QIcon("icons/cancel.png"), "", self)
		self.cancel_button.setGeometry(QtCore.QRect(280, 350, 30, 30))
		self.cancel_button.clicked.connect(self.hide)
		self.cancel_button.setIconSize(QtCore.QSize(30, 30))
		self.cancel_button.setObjectName("cancel")

		self.setStyleSheet("""#Form{background-color: rgb(100, 100, 100);}
									QPushButton {border: none;}
									QPushButton:hover {background-color: rgb(120, 120 ,120); /* make the default button prominent */}
	 """)
	
	def setCalendarDate(self, date):
		self.calendar.setSelectedDate(QtCore.QDate(date.year, date.month, date.day))
	
	def editCell(self, date, content = ""):
		
		self.setCalendarDate(date)
		self.text_box.setPlainText(content)
		
		self.show()
		self.activateWindow()
		self.text_box.setFocus()
	
	def submit(self):
		self.hide()
		self.submit_data.emit(self.calendar.selectedDate().toString("yyyy-MM-dd"), self.text_box.toPlainText())
