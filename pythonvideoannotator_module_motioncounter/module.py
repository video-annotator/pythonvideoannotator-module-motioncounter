import cv2
from pysettings import conf
from pythonvideoannotator_module_motioncounter.motion_counter import MotionCounter


class Module(object):

	def __init__(self):
		"""
		This implements the Path edition functionality
		"""
		super(Module, self).__init__()
		self.motion_window = MotionCounter(self)

		self.mainmenu[1]['Modules'].append(
			{'Calculate the objects motion': self.motion_window.show },			
		)

	def video_changed_evt(self):
		super(Module, self).video_changed_evt()
		self.motion_window.video_filename = self._video.value



	def add_dataset_evt(self, dataset):
		super(Module, self).add_dataset_evt(dataset)
		self.motion_window.add_dataset_evt(dataset)

	def remove_dataset_evt(self, dataset):
		super(Module, self).remove_dataset_evt(dataset)
		self.motion_window.remove_dataset_evt(dataset)

	def remove_object_evt(self, obj):
		super(Module, self).remove_object_evt(obj)
		self.motion_window.remove_object_evt(obj)


	######################################################################################
	#### IO FUNCTIONS ####################################################################
	######################################################################################

	