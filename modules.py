from PyQt5 import QtWidgets
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import *

class GifPlayer(QtWidgets.QWidget):
	def __init__(self, filename, pos, parent=None):
		QtWidgets.QWidget.__init__(self, parent)
		
		
		
		# Load the file into a QMovie
		self.movie = QMovie(filename, QByteArray(), self)
		
		self.movie.jumpToFrame(0)
		size = self.movie.currentImage().size()
		self.setGeometry(pos.x(), pos.y(), size.width(), size.height())

		self.movie_screen = QtWidgets.QLabel()
		# Make label fit the gif
		self.movie_screen.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		self.movie_screen.setAlignment(Qt.AlignCenter)

		# Create the layout
		main_layout = QtWidgets.QVBoxLayout()
		main_layout.addWidget(self.movie_screen)
		main_layout.setContentsMargins(0, 0, 0, 0)
		
		self.setLayout(main_layout)
		
		# Add the QMovie object to the label
		self.movie.setSpeed(100)
		self.movie_screen.setMovie(self.movie)
		
	def play(self):
		self.movie.start()
	
	def stop(self):
		self.movie.stop()
	
	def restart(self):
		self.movie.jumpToFrame(0)
	
	def pause(self):
		self.movie.setPaused(True)
		
	def unpause(self):
		self.movie.setPaused(False)	
	
	def reset(self):
		self.movie.stop()
		self.movie.jumpToFrame(0)