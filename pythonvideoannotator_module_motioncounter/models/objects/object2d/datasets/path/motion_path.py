import csv, cv2, os, numpy as np
from pysettings import conf

class MotionPath(object):

	def __init__(self, object2d):
		super(MotionPath, self).__init__(object2d)

		self._motion 		= []
		self._absmotion 	= []
		self._last_img  	= None
		self._last_diff 	= None
		self._mask			= None

		self.threshold 	= 5
		self.radius 	= 30

		

	def name_updated(self, newname):
		super(MotionPath, self).name_updated(newname)
		if hasattr(self,'mainwindow'): self.mainwindow.motion_window.update_datasets()

	def create_motion_tree_nodes(self):		
		self.treenode_motion = self.tree.create_child('motion', icon=conf.ANNOTATOR_ICON_MOTION, parent=self.treenode )
		variation_treenode 	 = self.tree.create_child('variation', icon=conf.ANNOTATOR_ICON_VELOCITY, parent=self.treenode_motion )


		self.tree.add_popup_menu_option(label='View on the timeline', function_action=self.__send_motion_to_timeline_event, item=self.treenode_motion, icon=conf.ANNOTATOR_ICON_TIMELINE)
		self.tree.add_popup_menu_option(label='View on the timeline', function_action=self.__send_motion_variation_to_timeline_event, item=variation_treenode, icon=conf.ANNOTATOR_ICON_TIMELINE)
		
		self.treenode_motion.win = variation_treenode.win = self

	def __send_motion_to_timeline_event(self):
		data = [(i,self.get_motion(i)) for i in range(len(self)) if self.get_motion(i) is not None]
		self.mainwindow.add_graph('{0} motion'.format(self.name), data)


	def __send_motion_variation_to_timeline_event(self):
		data = [(i,self.get_motion_variation(i)) for i in range(len(self)) if self.get_motion_variation(i) is not None]
		self.mainwindow.add_graph('{0} motion variation'.format(self.name), data)

	def get_motion_variation(self, index):
		m1 = self.get_motion(index-1)
		m2 = self.get_motion(index)
		if m1 and m2: return m2-m1
		else: return None

	def get_motion(self, index):
		if index<0 or index>=len(self._motion): return None
		return self._motion[index]

	def set_motion(self, index, value):
		if not hasattr(self,'treenode_motion'): self.create_motion_tree_nodes()
		
		if index>=len(self._motion): 
			for i in range(len(self._motion), index+1): self._motion.append(None)
		self._motion[index] = value

	def init(self):
		self._last_img  	= None
		self._last_diff 	= None
		

	def process(self, index, frame):
		pos = self.get_position(index)
		if pos is None: return None

		x,y		= pos
		cutx 	= int(round(x-self._radius))
		cuty 	= int(round(y-self._radius))
		cutxx 	= int(round(x+self._radius))
		cutyy 	= int(round(y+self._radius))
		if cutx<0: cutx=0; cutxx=self._radius*2
		if cuty<0: cuty=0; cutyy=self._radius*2

		small	= frame[cuty:cutyy, cutx:cutxx].copy()
		gray	= cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

		
		#print self._mask.shape, gray.shape
		small_masked = cv2.bitwise_and(self._mask, gray)
		if self._last_img==None: self._last_img = small_masked


		diff = cv2.absdiff(small_masked, self._last_img)
		self._last_diff = diff.copy()
		self._last_diff[self._last_diff>self._threshold] = 255

		diff[diff<=self._threshold] = 0
		diff[diff>self._threshold]	= 1

		self._absmotion.append( np.sum(diff) )

		diff = np.float32(small_masked)-np.float32(self._last_img)
		self.set_motion(index, np.sum(diff) )
		self._last_img 	= small_masked
		
		return self.get_motion(index)
		


	def draw_motion(self, index, frame, show_diff=True):
		pos = self.get_position(index)
		if pos is None: return None

		x,y		= pos
		
		if show_diff:
			cv2.circle(frame, (x,y), self._radius, (0,0,0), -1)
			frame[y-self._radius:y+self._radius, x-self._radius:x+self._radius] += cv2.merge( (self._last_diff, self._last_diff, self._last_diff) )
		else:
			cv2.circle(frame, (x,y), self._radius, (0,0,255))


	def get_csvrow(self, index): 
		res = super(MotionPath, self).get_csvrow(index)
		return res + [self.get_motion(index)]

	def load_csvrow(self, index, csvrow): 
		super(MotionPath, self).load_csvrow(index, csvrow)
		if len(csvrow)<5: return
		self.set_motion(index, None if (csvrow[3] is None or len(csvrow[3])==0 or csvrow[3]=='None') else float(csvrow[3]) )




	@property
	def radius(self): return self._radius
	@radius.setter
	def radius(self, value): 
		self._radius = value
		self._mask 	 = np.zeros( (self._radius*2, self._radius*2), dtype=np.uint8 ); 
		cv2.circle(self._mask, (self._radius, self._radius), self._radius, 255, -1 )
		self.init()
	
	@property
	def threshold(self): return self._threshold
	@threshold.setter
	def threshold(self, value): self._threshold = value