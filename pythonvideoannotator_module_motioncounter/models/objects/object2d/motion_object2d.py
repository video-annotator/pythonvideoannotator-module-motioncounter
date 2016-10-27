

class MotionObject2d(object):

	def __init__(self, objects_set):
		super(MotionObject2d, self).__init__(objects_set)
		
	######################################################################
	### EVENTS ###########################################################
	######################################################################

	def name_updated(self, newname):
		super(MotionObject2d, self).name_updated(newname)
		if hasattr(self,'mainwindow'): self.mainwindow.motion_window.update_datasets()