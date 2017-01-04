import sys, os, shutil, re, pyforms, numpy as np, cv2
from pysettings 		 import conf
from pyforms 			 import BaseWidget
from pyforms.Controls 	 import ControlFile
from pyforms.Controls 	 import ControlPlayer
from pyforms.Controls 	 import ControlButton
from pyforms.Controls 	 import ControlNumber
from pyforms.Controls 	 import ControlSlider
from pyforms.Controls 	 import ControlCheckBox
from pyforms.Controls 	 import ControlText
from pyforms.Controls 	 import ControlCheckBoxList
from pyforms.Controls 	 import ControlProgress
from PyQt4 import QtGui
from pythonvideoannotator_models.models.video.objects.object2d.datasets.path import Path

class MotionCounter(BaseWidget):

	def __init__(self, parent=None):
		BaseWidget.__init__(self, 'Motion counter', parent_win=parent)

		self.layout().setContentsMargins(10, 5, 10, 5)
		self.setMinimumHeight(300)
		self.setMinimumWidth(500)

		self._start 		= ControlNumber('Start on frame',0)
		self._end 			= ControlNumber('End on frame', 10)
		self._player			= ControlPlayer('Player')
		self._objects 			= ControlCheckBoxList('Objects')
		self._show_diff			= ControlCheckBox('Show diffs boxes')
		self._threshold_slider	= ControlSlider('Threshold', 5, 1, 255)
		self._radius_slider		= ControlSlider('Radius', 30, 1, 200)
		self._apply  			= ControlButton('Apply', checkable=True)
		self._progress  		= ControlProgress('Progress')

		
		self._formset = [
			('_objects',['_start','_end']), 
			'=',
			('_threshold_slider', '_radius_slider', '_show_diff'),
			'_player',
			'_apply',
			'_progress'
		]

		self.load_order = ['_start', '_end', '_threshold_slider', '_radius_slider', '_show_diff']


		self._player.processFrame 	= self.__process_frame

		self._threshold_slider.changed_event 	= self.__threshold_changed_event
		self._radius_slider.changed_event 	= self.__radius_changed_event
		self._apply.value 				= self.__apply_btn_event
		self._apply.icon 				= conf.ANNOTATOR_ICON_MOTION

		self._progress.hide()

		self._objects_list  = []
		self._selected_objs = []

	def __apply_btn_event(self):

		if self._apply.checked:
			self._start.enabled = False
			self._end.enabled = False
			self._objects.enabled = False
			self._show_diff.enabled = False
			self._threshold_slider.enabled = False
			self._player.enabled = False
			self._radius_slider.enabled = False
			self._apply.label = 'Cancel'

			self._player.video_index = 0
			cap = self._player.value



			start = int(self._start.value)
			end   = int(self._end.value)
			self._progress.min = start
			self._progress.max = end
			self._progress.show()

			cap.set(cv2.CAP_PROP_POS_FRAMES, start); 

			for index in range(start, end+1):
				res, frame = cap.read()
				if not res: break
				if not self._apply.checked: break

				index = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
				for obj in self.objects:
					motion = obj.process(index, frame)
					if motion is not None: obj.set_motion(index, motion)
				self._progress.value = index
		
			self._start.enabled = True
			self._end.enabled = True
			self._objects.enabled = True
			self._show_diff.enabled = True
			self._threshold_slider.enabled = True
			self._player.enabled = True
			self._radius_slider.enabled = True
			self._apply.label = 'Apply'
			self._apply.checked = False
			self._progress.hide()

	@property
	def video_filename(self): return None
	@video_filename.setter
	def video_filename(self, value): 
		self._player.value = value
		self._start.max = self._player.max
		self._end.max = self._player.max

	@property
	def objects(self): return self._objects.value
	@objects.setter
	def objects(self, value):  self._objects.value = value
	

	def add_dataset_event(self, dataset):
		if isinstance(dataset, Path):
			self._objects += [dataset, True]
			#self._objects_list.append(dataset)

	def removed_dataset_event(self, dataset):
		if isinstance(dataset, Path):
			self._objects -= dataset

	def removed_object_event(self, obj):
		items2remove = []
		for i, (item, checked) in enumerate(self._objects.items):
			if item.object2d==obj: items2remove.append(i)
		for i in sorted(items2remove,reverse=True): self._objects -= i


	###########################################################################
	### AUX FUNCTIONS #########################################################
	###########################################################################

	def update_datasets(self):
		items = self._objects.items
		self._objects.clear()
		self._objects.value = items
	
		

	def __process_frame(self, frame):
		index = self._player.video_index
		
		for obj in self.objects: obj.process(index, frame)
		for obj in self.objects: obj.draw_motion(index, frame, self._show_diff.value)

		return frame

	def __threshold_changed_event(self): self.threshold = self._threshold_slider.value
	def __radius_changed_event(self): 	 self.radius = self._radius_slider.value

	@property
	def radius(self): return self._radius_slider.value
	@radius.setter
	def radius(self, value): 
		for f in self.objects: f.radius = value

	@property
	def threshold(self): return self._threshold_slider.value
	@threshold.setter
	def threshold(self, value): 
		for f in self.objects: f.threshold = value


	

if __name__ == "__main__": pyforms.startApp(Main)