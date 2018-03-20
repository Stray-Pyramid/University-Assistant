# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'calender.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

#x, y, width, height

import sys, os

import datetime
import time
import imp
import traceback

from functools import partial

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import *

import settings

label_height = 40
label_width = 40

tabBar_height = 40
tabBar_width = 200

class MainWindow(QtWidgets.QMainWindow):
	tabs = {}
	tab_labels = []
	active_tab = None
	
	
	
	def __init__(self):
		super(MainWindow, self).__init__()
		
		self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool);
		self.setAttribute(QtCore.Qt.WA_TranslucentBackground);
		self.setMouseTracking(True)  
		self.leftMouseDown = False
		
		settings = QtCore.QSettings("calendar_settings")
		settings.beginGroup("MainWindow")
		self.move(settings.value("pos", QtCore.QPoint(200, 200)))
		settings.endGroup()
		
		self.setupUi()
		
		
	def setupUi(self):

		self.setObjectName("MainWindow")
		
		self.tabLabels_Box = QtWidgets.QFrame(self)
		self.tabLabels_Box.setObjectName("tabLabels_Box")
		self.tabLabels_Box.resize(QtCore.QSize(tabBar_width, tabBar_height))
		self.tabLabels_Box.setStyleSheet("""QFrame QPushButton{background-color: rgb(100, 100, 100); border: 2px solid white; border-top-left-radius: 10px; border-top-right-radius: 10px; border-bottom-width: 0px;}""")
		
		self.tabMenu_Box = QtWidgets.QFrame(self.tabLabels_Box)
		self.tabMenu_Box.setObjectName("tabMenu_Box")
		self.tabMenu_Box.setGeometry(tabBar_width - 25, 0, 25, label_height)
		self.tabMenu_Box.setStyleSheet("""QFrame{background-color: rgb(100, 100, 100); border: 2px solid white; border-top-left-radius: 5px; border-top-right-radius: 5px; border-bottom-width: 0px;} 
													   QPushButton {background-color: none; border: none;}""")
		
		self.minimize_btn = QtWidgets.QPushButton(QIcon("icons/minimize_icon.png"), "", self.tabMenu_Box)
		self.minimize_btn.setObjectName("minimize")
		self.minimize_btn.clicked.connect(self.showMinimized)
		self.minimize_btn.setGeometry(QtCore.QRect(2, 22, 20, 20))
		self.minimize_btn.setCursor(QtCore.Qt.PointingHandCursor)
		self.exit_btn = QtWidgets.QPushButton(QIcon("icons/close_icon.png"), "", self.tabMenu_Box)
		self.exit_btn.setObjectName("quit")
		self.exit_btn.clicked.connect(self.close_window)
		self.exit_btn.setGeometry(QtCore.QRect(2, 5, 20, 20))
		self.exit_btn.setCursor(QtCore.Qt.PointingHandCursor)
		
		self.mainview_Box = QtWidgets.QFrame(self)
		self.mainview_Box.setObjectName("mainView_Box")
		self.mainview_Box.setStyleSheet("QFrame#mainView_Box{border: 1px solid white;}")
		
	def addTab(self, tab_class):
		tab_name = type(tab_class).__name__[:-4]
		
		tabLabel = self.addTabLabel(tab_name, os.path.join(os.getcwd(), "icons", (tab_name + "_Icon.png")))
		
		print("Tab " + tab_name + " loaded")
		self.tabs[tab_name] = tab_class
		self.tabs[tab_name].tabLabel = tabLabel
		try:
			self.tabs[tab_name].hide()
			self.tabs[tab_name].setupUi(self.mainview_Box)
			self.tabs[tab_name].trigger_update()
		except:
			print("main.py: Something went wrong trying to initialize " + tab_name)
			traceback.print_exc()
			
		if self.active_tab == None:
			self.active_tab = tab_name
		
		
	def addTabLabel(self, name, img):
		tabLabel = TabLabel(name, img, self.tabLabels_Box)
		tabLabel.clicked.connect(partial(self.changeMainview, name))
		
		self.tab_labels.append(tabLabel)
		tab_position = len(self.tab_labels)
		
		tabLabel.move(tabBar_width - (((label_width- 1) * tab_position ) + 25), 0)
		
		return tabLabel
		
	def setTrayIcon(self, trayIcon):
		self.trayIcon = trayIcon
		
	def changeMainview(self, viewName):
		oldTab = self.active_tab
		oldViewSize = self.tabs[oldTab].size
		
		self.active_tab = viewName
		newViewSize = self.tabs[self.active_tab].size
		
		
		self.updatePosition(oldViewSize.width(), newViewSize.width())
		self.tabs[oldTab].hide()
		self.tabs[self.active_tab].show()
		
	def updatePosition(self, oldViewWidth, newViewWidth):
		window_pos = self.pos()
		
		self.mainview_Box.setGeometry(0, label_height, self.tabs[self.active_tab].size.width() + 2, self.tabs[self.active_tab].size.height() + 2)
		self.setGeometry(QtCore.QRect(window_pos.x() + (oldViewWidth - newViewWidth), window_pos.y(), self.mainview_Box.width(), self.mainview_Box.height() + tabBar_height))
		self.tabLabels_Box.move(self.mainview_Box.width() - tabBar_width, 0)
		
		
	#Dragging window functions	
	def mouseMoveEvent(self, e):
		
		if self.leftMouseDown == True:
			newLocation = self.windowStart - (self.dragStart - e.globalPos())
			self.move(newLocation)
			
	def mousePressEvent(self, e):
		if e.button() == QtCore.Qt.LeftButton:
			self.leftMouseDown = True
			self.dragStart = e.globalPos()
			self.windowStart = self.pos()
		
	def mouseReleaseEvent(self, e):
		if e.button() == QtCore.Qt.LeftButton:
			self.leftMouseDown = False
	
	def show_window(self):
		self.showNormal()
		self.activateWindow()
	
	def close_window(self):
	
		settings = QtCore.QSettings("calendar_settings");
		settings.beginGroup("MainWindow")
		settings.setValue("pos", self.pos())
		settings.endGroup()
		
		self.trayIcon.hide()
		
		app_instance = QtWidgets.QApplication.instance()
		app_instance.closeAllWindows()
		app_instance.quit()
		
class TabLabel(QtWidgets.QPushButton):
	
	normal_colour = "rgb(100, 100, 100)"
	notice_colour = "rgb(255, 233, 0)"
	alert_colour = "rgb(255, 0, 0)"
	
	border_colour = "rgb(255, 255, 255)"
	
	def __init__(self, module_name, module_img, parent):
		super(TabLabel, self).__init__()
		
		self.setParent(parent)
		
		self.setupUi(module_name, module_img)
		
	def setupUi(self, name, img):
		self.resize(label_width, label_height)
		
		self.setIcon(QIcon(img))
		self.setIconSize(QtCore.QSize(65,65))
		
		self.setCursor(QtCore.Qt.PointingHandCursor)
		self.setObjectName("tabLabel_" + name)
		
	def setColour(self, colour, border_colour = "white"):
		self.normal_colour = colour
		self.border_colour = border_colour
		
	def changeState(self, state):
		if state == settings.tabLabel_status.NORMAL:
			self.setStyleSheet("QPushButton{background-color: %s; border-color: %s}" % (self.normal_colour, self.border_colour))
		elif state == settings.tabLabel_status.NOTICE:
			self.setStyleSheet("QPushButton{background-color: %s; border-color: %s}" % (self.notice_colour, self.border_colour))
		elif state == settings.tabLabel_status.ALERT:
			self.setStyleSheet("QPushButton{background-color: %s; border-color: %s}" % (self.alert_colour, self.border_colour))
			
		
class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    
	normalize = QtCore.pyqtSignal()
	
	def __init__(self, icon, toolTip, parent=None):
		QtWidgets.QSystemTrayIcon.__init__(self, parent)
		self.setIcon(QIcon(icon))
		self.setToolTip(toolTip)

		self.activated.connect(self.click_trap)

	def click_trap(self, value):
		if value == self.DoubleClick:
			self.normalize.emit()

		
def main():

	app = QtWidgets.QApplication(sys.argv)
	Module_Display = MainWindow()
	
	modules_location = (os.getcwd() + "\\tabs")
	
	modules = [imp.load_source(filename, os.path.join(modules_location, filename)) 
					for filename in os.listdir(modules_location) if filename.endswith('.py')]
	
	for module in modules:
		print(module.__name__)
		module = getattr(module, module.__name__[:-3] + "_Tab")()
		Module_Display.addTab(module)
	
	trayIcon = SystemTrayIcon(QIcon("icons/agglomerator.png"), "Agglomerator", app) 
	trayIcon.normalize.connect(Module_Display.show_window)
	trayIcon.show()
	
	app.setApplicationDisplayName('Agglomerator')
	app.setWindowIcon(QIcon("icons/agglomerator.png"))
	app.setQuitOnLastWindowClosed(False)
	 
	Module_Display.setTrayIcon(trayIcon)
	Module_Display.updatePosition(0, 0)
	Module_Display.tabs[Module_Display.active_tab].show()
	Module_Display.show()
	
	sys.exit(app.exec_())
	

if __name__=='__main__':
    main()

