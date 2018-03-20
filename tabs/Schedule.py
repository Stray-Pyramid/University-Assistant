import datetime
import time
import calendar
import math

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import *

import settings
from threads import DatabaseFetcher
from modules import GifPlayer

normal_cell_size = QtCore.QSize(114, 34)
day_cell_size = QtCore.QSize(normal_cell_size.width(), 27)
time_cell_size = QtCore.QSize(55, normal_cell_size.height())

classes_query = """ SELECT * FROM "Database"."Table" WHERE DATE_TRUNC('day', "time_start") >= DATE %s AND DATE_TRUNC('day', "time_start") <= DATE %s; """
planner_query = """ SELECT * FROM "Database"."Table" WHERE DATE_TRUNC('day', "start_date") >= DATE %s AND DATE_TRUNC('day', "start_date") <= DATE %s; """

#date_override = "2018-03-12"

class Schedule_Tab(QtWidgets.QFrame):
	
	size = QtCore.QSize(time_cell_size.width()+1 + ((normal_cell_size.width()+1) * settings.schedule["num_of_days"]), 623)
	cells = []
	schedule_cells = []
	
	queryQueue = []
	
	def __init__(self):
		super(Schedule_Tab, self).__init__()
		
		self.tabLabel = None

		self.Input_Window = Cell_Input_Widget()
		self.Input_Window.new_cell_signal.connect(self.new_cell)
		self.Input_Window.update_cell_signal.connect(self.update_cell)
		self.Input_Window.delete_cell_signal.connect(self.delete_cell)
		
		self.updating = False
		self.thread = DatabaseFetcher()
		self.thread.data_ready.connect(self.handle_db_response)
		
		self.minute_timer = QtCore.QTimer(self)
		self.minute_timer.timeout.connect(self.schedule_alert_update)
		self.minute_timer.setSingleShot(False)
		self.minute_timer.start(60 * 1000)
		
		self.leftMouseDown = False
		self.leftMouseDownPosition = None
		self.selectedColumn = None
		self.startSegment = None
		self.numOfSegments = 0
		self.selectionHighlightBox = QtWidgets.QLabel(self)
		self.selectionHighlightBox.setStyleSheet("QLabel{background-color: rgba(175, 175, 175, 0.5)}")
		
	def setupUi(self, parent = None):
		self.setGeometry(1,1, self.size.width(), self.size.height())
		
		self.setParent(parent)
		self.setObjectName("centralwidget")
		
		self.setStyleSheet("""#centralwidget{background-color: #537EB0}
							#day_label{color: white; font-size: 15px}
							QPushButton#refresh_btn {background-color: none; border: none;}
							""")
		
		#Set background-color of cells
		for column in range(0, settings.schedule["num_of_days"] + 1):
			column_cells = []
			for row in range(0, 18):
				cell = QtWidgets.QFrame(self)
				column_cells.append(cell)
				
				if row == 0 and column != 0:
					# Day name cells
					cell.setGeometry(time_cell_size.width() + 2 + ((day_cell_size.width() + 1) * (column-1)), 0, day_cell_size.width(), day_cell_size.height())
					cell.setStyleSheet("QFrame{background-color: #A2C1E8;}")
					
				elif column == 0:
					# Time cells
					if row == 0:
						cell.setGeometry(0, 0, time_cell_size.width(), day_cell_size.height())
					else:
						cell.setGeometry(0, day_cell_size.height() + 2 + ((time_cell_size.height() + 1) * (row - 1)), time_cell_size.width(), time_cell_size.height())
					cell.setStyleSheet("QFrame{background-color: #A2C1E8}")
					
				else:
					#Everything else
					cell.setGeometry(time_cell_size.width() + 2 + ((day_cell_size.width() + 1) * (column-1)), day_cell_size.height() + 2 + ((normal_cell_size.height() + 1) * (row - 1)), normal_cell_size.width(), normal_cell_size.height())
					cell.setStyleSheet("QFrame{background-color: #EAEAEA}")
					
			self.cells.append(column_cells)
		
		#Add day labels
		for i in range(0, settings.schedule["num_of_days"]):
			self.cells[i + 1][0].day_label = QtWidgets.QLabel("N/A", self.cells[i + 1][0])
			self.cells[i + 1][0].day_label.resize(day_cell_size)
			self.cells[i + 1][0].day_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
			self.cells[i + 1][0].day_label.setObjectName("day_label")
		
		#Add time labels
		for row in range(0, 17):
			time_cell = self.cells[0][row + 1]
			
			if row <= 6:
				time_cellhour_label = QtWidgets.QLabel(str(row + 6), self.cells[0][row + 1])
			else:
				time_cellhour_label = QtWidgets.QLabel(str(row - 6), self.cells[0][row + 1])
				
			time_cellhour_label.setGeometry(13, 7, 25, 17)
			time_cellhour_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
			time_cellhour_label.setStyleSheet("QLabel{color: white; font-size: 20px}")
			
			if row == 6:
				time_cellminute_label = QtWidgets.QLabel("PM", self.cells[0][row + 1])
			else:
				time_cellminute_label = QtWidgets.QLabel("00", self.cells[0][row + 1])
				
			time_cellminute_label.setGeometry(39, 8, 14, 12)
			time_cellminute_label.setAlignment(QtCore.Qt.AlignLeft)
			time_cellminute_label.setStyleSheet("QLabel{color: white; font-size: 9px}")
			
		#Refresh Button
		self.refresh_icon = GifPlayer("icons/ajax-loader.gif", QtCore.QPoint(0, 0), self)
		self.refresh_icon.setCursor(QtCore.Qt.PointingHandCursor)
		self.refresh_btn = QtWidgets.QPushButton(self.refresh_icon)
		self.refresh_btn.clicked.connect(self.trigger_update)
		self.refresh_btn.setGeometry(QtCore.QRect(0, 0, 20, 20))
		self.refresh_btn.setObjectName("refresh_btn")
	
	
	def trigger_update(self):
		#Delete all existing cells
		for cell in self.schedule_cells:
			cell.delete()
		self.schedule_cells = []
		
		#Set date and time
		self.update_ui()
		
		current_date = self.get_current_date()
		future_date = current_date + datetime.timedelta(days = (settings.schedule["num_of_days"] - 1))
		
		#Clear query queue, stop db thread
		
		#Queue database requests
		self.queryQueue.append([classes_query, (current_date.strftime("%Y-%m-%d"), future_date.strftime("%Y-%m-%d")), "S_classes"])
		self.queryQueue.append([planner_query, (current_date.strftime("%Y-%m-%d"), future_date.strftime("%Y-%m-%d")), "S_planner"])
		self.runQueue()
		
		
	
	def handle_db_response(self, result, data, reference):
		if result == 'failure':
			print("Schedule: db response failure")
			self.updating = False
			return
		
		if (reference == "S_planner" or reference == "S_classes"):
			print("Schedule: Got cell data from database")
			self.populate_schedule_cells(data)
			
		elif type(reference) == "int":
			#id from row that was inserted
			for cell in self.schedule_cells:
				if cell.id == reference:
					cell.id == data[0]
					break
			
		print("Query complete: " + reference)
		del self.queryQueue[0]
		self.runQueue()

		
	def update_ui(self):
		
		current_date = self.get_current_date()
		
		#column date
		for i in range(0, settings.schedule["num_of_days"]):
			self.cells[i + 1][0].day_label.setText((current_date + datetime.timedelta(days = i)).strftime("%A, %d"))
		
		#background colour of table, dependent on day
		current_date = self.get_current_date()
		for column in range(0, settings.schedule["num_of_days"]):
			is_weekend = (current_date + datetime.timedelta(days = column)).weekday() >= 5
			for row in range(1, 18):
				if is_weekend:
					self.cells[column + 1][row].setStyleSheet("QFrame{background-color: #CCCCCC}")
				else:
					self.cells[column + 1][row].setStyleSheet("QFrame{background-color: #EAEAEA}")
		
	
	def populate_schedule_cells(self, data):
		
		for cell_data in data:
			
			if type(cell_data[1]).__name__ == 'str':
				#S_classes
				id = cell_data[0]
				room = cell_data[1]
				subject = cell_data[4]
				paper_num = cell_data[3]
				start_time = cell_data[5]
				end_time = cell_data[6]
				colour = cell_data[4]
								
								
				cell = Timetable_Cell(id, "%s %s\n%s" % (room, subject, paper_num), settings.schedule["subject_colours"][colour], start_time, end_time, self, locked = True)
				cell.edit_cell_signal.connect(self.edit_cell)
				self.schedule_cells.append(cell)
				
			else:
				#S_planner
				id = cell_data[0]
				start_time = cell_data[1]
				end_time = cell_data[2]
				content = cell_data[3]
				colour = cell_data[4]
				
				cell = Timetable_Cell(id, content, colour, start_time, end_time, self)
				cell.edit_cell_signal.connect(self.edit_cell)
				self.schedule_cells.append(cell)
	
	def schedule_alert_update(self):
		
		#If there is a class currently happening, change tab status to NOTICE
		print("schedule_alert_update triggered.")
		for i in range(0, len(self.schedule_cells)):
			if self.schedule_cells[i].start_datetime < datetime.datetime.now() and self.schedule_cells[i].end_datetime > datetime.datetime.now():
				self.tabLabel.changeState(settings.tabLabel_status.NOTICE)
				return
		
		#Else, set it to normal status.
		self.tabLabel.changeState(settings.tabLabel_status.NORMAL)
		
		
		
	def get_current_date(self):
		try:
			return datetime.datetime.strptime(date_override, "%Y-%m-%d")
		except:
			return datetime.date.today()
	
	def mousePressEvent(self, e):
		
		if ((e.button() == QtCore.Qt.LeftButton) and (e.pos().x() >= time_cell_size.width() and e.pos().y() >= day_cell_size.height())):
			self.leftMouseDown = True
			self.leftMouseDownPosition = e.pos()
			self.selectedColumn = math.floor((e.pos().x() - (time_cell_size.width()+2))/ (normal_cell_size.width()+1))
			self.selectedSegment = math.floor((e.pos().y() - (day_cell_size.height()+2)) / ((normal_cell_size.height()+1) / 4))
			self.numOfSegments = 0
			
			self.selectionHighlightBox.setGeometry(0, 0, 0, 0)
			self.selectionHighlightBox.show()
		else:
			e.ignore()	
		
	def mouseMoveEvent(self, e):
	
		if self.leftMouseDown:
						
			#Calculate geometry of highlight box
			xPos = (self.selectedColumn * (normal_cell_size.width()+1)) + time_cell_size.width()+2
			width = normal_cell_size.width()
			
			yPos = (self.selectedSegment * ((normal_cell_size.height()+1)) / 4) + day_cell_size.height()+2
			numOfSegments = math.ceil((e.pos().y() - self.leftMouseDownPosition.y()) / (normal_cell_size.height()/4))
			height = ((normal_cell_size.height() + 1)/4) * numOfSegments
			
			#Check for conflicts with existing schedule cells, no two cells should intersect
			hasConflict = self.checkScheduleConflicts(self.selectedColumn, self.selectedSegment, numOfSegments)
			if not hasConflict:
			
				#Update highlight box geometry
				if e.pos().y() < self.leftMouseDownPosition.y():
					#Inverted
					yPos = yPos + height
					height = abs(height) + ((normal_cell_size.height() + 1)/4)
				
				self.numOfSegments = numOfSegments
				self.selectionHighlightBox.setGeometry(xPos, yPos, width, height)
				self.selectionHighlightBox.raise_()
			
		else:
			e.ignore()
	
	def checkScheduleConflicts(self, selectedColumn, selectedSegment, numOfSegments):
		if numOfSegments < 0:
				selectedSegment = selectedSegment + numOfSegments
				numOfSegments = abs(numOfSegments) + 1
		
		column_datetime = datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days = selectedColumn), datetime.time.min)
		start_datetime = column_datetime + (datetime.timedelta(hours = 6) + datetime.timedelta(minutes = (selectedSegment * 15)))
		end_datetime = start_datetime + datetime.timedelta(minutes = (15 * numOfSegments))
		
		# No two cells should happen at the same time
		
		for schedule_cell in self.schedule_cells:
			if schedule_cell.start_datetime < start_datetime and schedule_cell.end_datetime > start_datetime:
				return True
			elif schedule_cell.start_datetime < end_datetime and schedule_cell.end_datetime > end_datetime:
				return True
			elif schedule_cell.start_datetime >= start_datetime and schedule_cell.end_datetime <= end_datetime:
				return True
		
		#Check if out of boundary
		if not (start_datetime >= (column_datetime + datetime.timedelta(hours = 6)) and end_datetime <= (column_datetime + datetime.timedelta(hours = 23))):
			return True
		
		return False
	
	def mouseReleaseEvent(self, e):
	
		if e.button() == QtCore.Qt.LeftButton and self.leftMouseDown:
			self.leftMouseDown = False
			print("Selection began at %s, %s" % (self.leftMouseDownPosition.x(), self.leftMouseDownPosition.y()))
			print("Selected ended at %s, %s" % (e.pos().x(), e.pos().y()))
			
			if self.numOfSegments == 0:
				return
			
			#Get information
			selectedColumn = self.selectedColumn
			selectedSegment = self.selectedSegment
			numOfSegments = self.numOfSegments
			
			hasConflict = self.checkScheduleConflicts(selectedColumn, selectedSegment, numOfSegments)
			if hasConflict:
				#Hide and ignore selection
				self.selectionHighlightBox.hide()
				return
				
			
			
			if numOfSegments < 0:
				selectedSegment = selectedSegment + numOfSegments
				numOfSegments = abs(numOfSegments) + 1
			
			#Calculate date and time
			#6am to 10pm
			date = datetime.date.today() + datetime.timedelta(days = selectedColumn)
			start_datetime = datetime.datetime.combine(date, datetime.time.min) + (datetime.timedelta(hours = 6) + datetime.timedelta(minutes = (selectedSegment * 15)))
			end_datetime = start_datetime + datetime.timedelta(minutes = (15 * numOfSegments))
			
			print("selectedSegment: %s, numOfSegments: %s" % (selectedSegment, numOfSegments))
			print("Start date: %s, End date: %s" % (start_datetime, end_datetime))
			
			#New input window based on date and time
			self.Input_Window.new_schedule_cell(start_datetime, end_datetime)
			
			#Hide selection box
			self.selectionHighlightBox.hide()
		else:
			e.ignore()
	
	def edit_cell(self, cell):
		self.Input_Window.existing_schedule_cell(cell)
	
	def new_cell(self, start_datetime, end_datetime, context, colour):
		
		#Send data to database
		current_datetime = datetime.datetime.now().strftime("%x %X")
		insert_cell_query = """INSERT INTO "Schema"."Table" (start_date, end_date, content, colour, date_added) VALUES (%s, %s, %s, %s, %s) RETURNING id"""
		
		#find next available id
		highest_id = 0
		for cell in self.schedule_cells:
			if cell.id > highest_id:
				highest_id = cell.id
		
		
		self.queryQueue.append([insert_cell_query, (start_datetime, end_datetime, context, colour, current_datetime), str(highest_id + 1)])
		self.runQueue()
		
		cell = Timetable_Cell(highest_id + 1, context, colour, start_datetime, end_datetime, self)
		cell.edit_cell_signal.connect(self.edit_cell)
		self.schedule_cells.append(cell)
			
	def update_cell(self, cell, content, colour):
		update_cell_query = """ UPDATE "Schema"."Table" SET content = %s, colour = %s WHERE id = %s """
		
		cell.set_content(content)
		cell.set_colour(colour)
		
		self.queryQueue.append([update_cell_query, [content, colour, cell.id], "update"])
		self.runQueue()
		
		
	def delete_cell(self, cell):
		delete_cell_query = """ DELETE FROM "Schema"."Table" WHERE id = %s """
		
		cell_id = cell.id
		cell.delete()
		for current_cell in self.schedule_cells[:]:
			if current_cell == cell:
				self.schedule_cells.remove(current_cell)
				print("Cell wrapper deleted")
		
		self.queryQueue.append([delete_cell_query, [cell_id], "delete"])
		self.runQueue()
			
	def runQueue(self):
		if(len(self.queryQueue) > 0):

			if(self.thread.isRunning() == False):
				self.thread.execute(self.queryQueue[0])
				self.refresh_icon.play()
				self.updating = True
		
		else:
			self.refresh_icon.reset()
			self.updating = False
		
class Timetable_Cell(QtWidgets.QFrame):
	
	cell_style = "#timetable_cell{border: 1px solid black; background-color: %s; border-radius: 5px;}"
	colourTag_style = "QFrame{border: 1px solid black; border-top-left-radius: 5px; border-bottom-left-radius: 5px; background-color: %s };"
	
	edit_cell_signal = QtCore.pyqtSignal(object)
	
	
	
	def __init__(self, id, content, colour, start_datetime, end_datetime, parent = None, locked = False):
		super(Timetable_Cell, self).__init__()
		
		self.id = id
		self.locked = locked
		
		self.start_datetime = start_datetime.replace(tzinfo=None)
		self.end_datetime = end_datetime.replace(tzinfo=None)
			
		current_date = datetime.date.today()
		
		hour_of_day = start_datetime.hour + (start_datetime.minute / 60)		
		day_displacement = (start_datetime.date() - current_date).days
		
		cell_width = 112
		cell_height = (((end_datetime - start_datetime).total_seconds() / 3600) * 34)
				
		cell_pos_x = 57 + (day_displacement * 115)
		cell_pos_y = 29 + ((hour_of_day - 6) * 35) 
		
		super(Timetable_Cell, self).__init__()
		self.setParent(parent)
		self.setGeometry(cell_pos_x, cell_pos_y, cell_width, cell_height)
		self.setObjectName("timetable_cell")
		self.setStyleSheet(self.cell_style % "white")
		self.setToolTip(content)

		drop_shadow = QtWidgets.QGraphicsDropShadowEffect(self)
		drop_shadow.setBlurRadius(5)
		drop_shadow.setOffset(2, 2)
		self.setGraphicsEffect(drop_shadow)
		
		self.colour_tag = QtWidgets.QFrame(self)
		self.colour_tag.setGeometry(0,0, 8, cell_height)
		self.colour_tag.setStyleSheet(self.colourTag_style % colour)
		self.colour = colour
		
		self.cell_label = QtWidgets.QLabel(content, self)
		self.cell_label.setGeometry(10, 0, 100, cell_height)
		self.cell_label.setStyleSheet("QLabel{font-size: 9px;}")
		self.cell_label.setWordWrap(True)
		
		self.show()
	
	def set_content(self, content):
		self.setToolTip(content)
		self.cell_label.setText(content)
	
	def set_colour(self, colour):
		self.colour_tag.setStyleSheet(self.colourTag_style % colour)
		self.colour = colour
	
	def delete(self):
		self.setGraphicsEffect(None)
		self.deleteLater()
	
	def mousePressEvent(self, e):
		if not self.locked:
			self.edit_cell_signal.emit(self)
			
	def enterEvent(self, e):
		if not self.locked:
			self.setStyleSheet(self.cell_style % "Gainsboro")
	
	def leaveEvent(self, e):
		if not self.locked:
			self.setStyleSheet(self.cell_style % "white")
		
class Cell_Input_Widget(QtWidgets.QWidget):
	
	new_cell_signal = QtCore.pyqtSignal(datetime.datetime, datetime.datetime, str, str)
	update_cell_signal = QtCore.pyqtSignal(object, str, str)
	delete_cell_signal = QtCore.pyqtSignal(object)
	
	def __init__(self):	
		super(Cell_Input_Widget, self).__init__()
		
		self.selected_colour = None
		self.mode = None
		self.selected_cell = None
		
		self.setupUi()
		
	def setupUi(self):
		self.setObjectName("Form")
		self.setWindowTitle("Form")
		self.resize(320, 185)
		self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
	
		self.start_date_input = QtWidgets.QDateTimeEdit(self)
		self.start_date_input.setGeometry(QtCore.QRect(10, 10, 240, 30))
		
		self.end_date_input = QtWidgets.QDateTimeEdit(self)
		self.end_date_input.setGeometry(QtCore.QRect(10, 45, 240, 30))
		
		self.colour_box = QtWidgets.QPushButton(self)
		self.colour_box.setGeometry(QtCore.QRect(10, 80, 240, 30))
		self.colour_box.setCursor(QtCore.Qt.PointingHandCursor)
		self.colour_box.clicked.connect(self.get_colour)
		self.colour_box.setObjectName("button")
		
		self.context_input = QtWidgets.QPlainTextEdit(self)
		self.context_input.setGeometry(QtCore.QRect(10, 115, 240, 60))
		self.context_input.setPlaceholderText("Whats happening?")
		
		self.submit_button = QtWidgets.QPushButton(QIcon("icons/tick.png"), "", self)
		self.submit_button.setGeometry(QtCore.QRect(280, 10, 30, 30))
		self.submit_button.clicked.connect(self.submit)
		self.submit_button.setIconSize(QtCore.QSize(30, 30))
		self.submit_button.setCursor(QtCore.Qt.PointingHandCursor)
		self.submit_button.setObjectName("button")
		
		self.delete_button = QtWidgets.QPushButton(QIcon("icons/delete.png"), "", self)
		self.delete_button.setGeometry(QtCore.QRect(280, self.size().height() - 80, 30, 30))
		self.delete_button.clicked.connect(self.delete)
		self.delete_button.setIconSize(QtCore.QSize(30, 30))
		self.delete_button.setCursor(QtCore.Qt.PointingHandCursor)
		self.delete_button.setObjectName("button")
		
		self.cancel_button = QtWidgets.QPushButton(QIcon("icons/cancel.png"), "", self)
		self.cancel_button.setGeometry(QtCore.QRect(280, self.size().height() - 40, 30, 30))
		self.cancel_button.clicked.connect(self.hide)
		self.cancel_button.setIconSize(QtCore.QSize(30, 30))
		self.cancel_button.setCursor(QtCore.Qt.PointingHandCursor)
		self.cancel_button.setObjectName("button")
		
		self.setStyleSheet("""#Form{background-color: rgb(100, 100, 100);}
							  #Form QPushButton#button {border: none;}
							  #Form QPushButton#button:hover {background-color: rgb(120, 120 ,120);}
		""")
		
	def new_schedule_cell(self, start_datetime, end_datetime):
		self.mode = 'new'
		self.delete_button.hide()
		
		self.start_date_input.setDateTime(start_datetime)
		self.end_date_input.setDateTime(end_datetime)
		self.colour_box.setStyleSheet("QPushButton{background-color: white}")
		self.context_input.setPlainText("")
		self.selected_colour = "#FFFFFF"
		self.show()
	
	def existing_schedule_cell(self, cell):
		self.mode = 'edit'
		self.delete_button.show()
		
		self.selected_cell = cell
		
		self.start_date_input.setDateTime(cell.start_datetime)
		self.end_date_input.setDateTime(cell.end_datetime)
		self.colour_box.setStyleSheet("QPushButton{background-color: %s}" % cell.colour)
		self.context_input.setPlainText(cell.cell_label.text())
		self.selected_colour = cell.colour
		self.show()
		
	
	def get_colour(self):
		selected_colour = QtWidgets.QColorDialog.getColor()
		self.selected_colour = selected_colour.name()
		if selected_colour:
			self.colour_box.setStyleSheet("QPushButton{background-color: " + selected_colour.name() + "}")
	
	def submit(self):			
		
		if self.mode == "new":
			#start_datetime, end_datetime, context, selected_colour
			start_datetime = self.start_date_input.dateTime().toPyDateTime()
			end_datetime = self.end_date_input.dateTime().toPyDateTime()
			
			self.new_cell_signal.emit(start_datetime, end_datetime, self.context_input.toPlainText(), self.selected_colour)
		
		elif self.mode == "edit":
			self.update_cell_signal.emit(self.selected_cell, self.context_input.toPlainText(), self.selected_colour)
			
		self.hide()
		
	def delete(self):
		confirmation_msg = "Are you sure you want to delete this cell?"
		reply = QtWidgets.QMessageBox.question(self, 'Delete cell', confirmation_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

		if reply == QtWidgets.QMessageBox.Yes:
			self.delete_cell_signal.emit(self.selected_cell)
			self.hide()
		
		
		