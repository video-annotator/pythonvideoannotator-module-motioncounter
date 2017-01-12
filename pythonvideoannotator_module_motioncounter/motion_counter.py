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
from pyforms.Controls 	 import ControlEmptyWidget
from pyforms.Controls 	 import ControlProgress
from PyQt4 import QtGui

from pythonvideoannotator_models_gui.dialogs import DatasetsDialog

from pythonvideoannotator_models_gui.models.video.objects.object2d.datasets.contours import Contours
from pythonvideoannotator_models_gui.models.video.objects.object2d.datasets.path import Path

class MotionCounter(BaseWidget):

	def __init__(self, parent=None):
		BaseWidget.__init__(self, 'Motion counter', parent_win=parent)

		self.layout().setContentsMargins(10, 5, 10, 5)
		self.setMinimumHeight(300)
		self.setMinimumWidth(500)

		self._player	= ControlPlayer('Player')
		self._datasets 	= ControlEmptyWidget('Objects', DatasetsDialog() )
		self._show_diff	= ControlCheckBox('Show diffs boxes')
		self._threshold	= ControlSlider('Threshold', 5, 1, 255)
		self._radius	= ControlSlider('Radius', 30, 1, 200)
		self._apply  	= ControlButton('Apply', checkable=True)
		self._progress 	= ControlProgress('Progress')

		
		self._formset = [
			'_datasets', 
			'=',
			('_threshold', '_radius', '_show_diff'),
			'_player',
			'_apply',
			'_progress'
		]

		self.load_order = ['_threshold', '_radius', '_show_diff']

		self._datasets.value.datasets_filter   				= lambda x: isinstance(x, (Contours, Path) )
		self._player.process_frame_event 					= self.__process_frame_event
		self._datasets.value.video_selection_changed_event 	= self.__video_selection_changed_event
		
		self._apply.value 		= self.__apply_btn_event
		self._apply.icon 		= conf.ANNOTATOR_ICON_MOTION
		self._progress.hide()

	###########################################################################
	### EVENTS ################################################################
	###########################################################################

	def __video_selection_changed_event(self):
		video = self._datasets.value.selected_video
		if video is not None: self._player.value = video.video_capture

	def __process_frame_event(self, frame):
		index 			= self._player.video_index
		selected_video 	= self._datasets.value.selected_video
		radius 			= self._radius.value
		threshold 		= self._threshold.value

		show_diff 		= self._show_diff.value

		if show_diff:
			circular_mask = np.zeros( (radius*2, radius*2), dtype=np.uint8 )
			cv2.circle(circular_mask, (radius, radius), radius, 255, -1 )
			
		for video, (begin, end), datasets in self._datasets.value.selected_data:
			if video != selected_video: continue

			for dataset in datasets:
				pos = dataset.get_position(index)
				if pos is None: continue

				if show_diff:
					x,y	  = pos
					cutx  = int(round(x-radius))
					cuty  = int(round(y-radius))
					cutxx = int(round(x+radius))
					cutyy = int(round(y+radius))
					if cutx<0: cutx=0; cutxx = radius*2
					if cuty<0: cuty=0; cutyy = radius*2

					small 		 = frame[cuty:cutyy, cutx:cutxx].copy()
					small_gray   = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
					small_masked = cv2.bitwise_and(circular_mask, small_gray)

					if 	not hasattr(self, '_last_small_masked') or \
						self._last_small_masked==None or \
						self._last_small_masked.shape[0]*self._last_small_masked.shape[1]!=small_masked.shape[0]*small_masked.shape[1]: 
						self._last_small_masked = small_masked

					diff = cv2.absdiff(small_masked, self._last_small_masked)
					diff[diff<threshold]  = 0
					diff[diff>=threshold] = 255

					cv2.circle(frame, pos, radius, (0,0,0), -1)
					frame[y-radius:y+radius, x-radius:x+radius] += cv2.merge( (diff, diff, diff) )
				else:
					cv2.circle(frame, pos, radius, (0,0,255), 2)
		return frame
			
	def __apply_btn_event(self):

		if self._apply.checked:
			self._datasets.enabled 	= False
			self._show_diff.enabled = False
			self._threshold.enabled = False
			self._player.enabled 	= False
			self._radius.enabled 	= False
			self._player.stop()
			self._apply.label 		= 'Cancel'

			total_2_analyse  = 0
			for video, (begin, end), datasets in self._datasets.value.selected_data:
				total_2_analyse += end-begin+1

			self._progress.min = 0
			self._progress.max = total_2_analyse
			self._progress.show()

			radius    = self._radius.value
			threshold = self._threshold.value
			circular_mask = np.zeros( (radius*2, radius*2), dtype=np.uint8 )
			cv2.circle(circular_mask, (radius, radius), radius, 255, -1 )
			

			count = 0
			for video, (begin, end), datasets in self._datasets.value.selected_data:
				begin = int(begin)
				end = int(end)+1

				capture = cv2.VideoCapture(video.filepath)
				capture.set(cv2.CAP_PROP_POS_FRAMES, begin)

				last_small_masked = [None for x in datasets]

				for index in range(begin, end):
					res, frame = capture.read()
					if not res: break
					if not self._apply.checked: break

					for dataset_index, dataset in enumerate(datasets):
						pos = dataset.get_position(index)
						if pos is None: continue

						x,y	  = pos
						cutx  = int(round(x-radius))
						cuty  = int(round(y-radius))
						cutxx = int(round(x+radius))
						cutyy = int(round(y+radius))
						if cutx<0: cutx=0; cutxx = radius*2
						if cuty<0: cuty=0; cutyy = radius*2

						small 		 = frame[cuty:cutyy, cutx:cutxx].copy()
						small_gray   = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
						small_masked = cv2.bitwise_and(circular_mask, small_gray)

						if last_small_masked[dataset_index]==None: last_small_masked[dataset_index] = small_masked

						diff = cv2.absdiff(small_masked, last_small_masked[dataset_index])
						diff[diff<threshold]  = 0
						diff[diff>=threshold] = 1

						motion = np.sum(diff)
						dataset.set_motion(index, motion)

					self._progress.value = count
					count += 1
		
			self._datasets.enabled 	= True
			self._show_diff.enabled = True
			self._threshold.enabled = True
			self._player.enabled 	= True
			self._radius.enabled 	= True
			self._apply.label 		= 'Apply'
			self._apply.checked 	= False
			self._progress.hide()


	

	




	

if __name__ == "__main__": pyforms.start_app(MotionCounter)