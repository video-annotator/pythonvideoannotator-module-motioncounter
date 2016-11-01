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
			{'Motion': self.motion_window.show, 'icon':conf.ANNOTATOR_ICON_MOTION },			
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

	
	def save(self, data, project_path=None):
		data = super(Module, self).save(data, project_path)
		data['motion-settings'] = self.motion_window.save({})
		return data

	def load(self, data, project_path=None):
		super(Module, self).load(data, project_path)
		if 'motion-settings' in data: self.motion_window.load(data['motion-settings'])
