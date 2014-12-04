

class GliderProperties(object):
	def __init__(self):
		self.glide_ratio = 20
		self.termToLandingAlt = 1000;
	
	def evalMaxGlide(self, delta_alt):
		return self.glide_ratio*delta_alt
		
	def evalReqGlideAlt(self, dist):
		return round(dist/self.glide_ratio)
	
	def getMinWorkAlt(self):
		return self.termToLandingAlt
