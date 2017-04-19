#Copyright 2017 Tyler Spivey <tspivey@pcdesk.net>
#Released under the GPLv2. See copying.txt.
from functools import wraps
import globalPluginHandler
import ui
import tones
import config
import api
import textInfos
import addonHandler

addonHandler.initTranslation()

def finally_(func, final):
	"""Calls final after func, even if it fails."""
	def wrap(f):
		@wraps(f)
		def new(*args, **kwargs):
			try:
				func(*args, **kwargs)
			finally:
				final()
		return new
	return wrap(final)

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	scriptCategory = _("Virtual Copy")

	def __init__(self):
		globalPluginHandler.GlobalPlugin.__init__(self)
		self.toggling = False
		self.__toggle_gestures = {}
		for c in "klw":
			self.__toggle_gestures["KB:%s" % c] = "toggleX"
			self.__toggle_gestures["KB:NVDA+%s" % c] = "toggleX"
		#home and end
		self.__toggle_gestures["KB:home"] = "copy_to_start"
		self.__toggle_gestures["KB:end"] = "copy_to_end"

	def getScript(self, gesture):
		if not self.toggling:
			return globalPluginHandler.GlobalPlugin.getScript(self, gesture)
		script = globalPluginHandler.GlobalPlugin.getScript(self, gesture)
		if not script:
			script = finally_(self.script_error, self.finish)
		return finally_(script, self.finish)

	def finish(self):
		self.toggling = False
		self.clearGestureBindings()

	def script_error(self, gesture):
		tones.beep(120, 100)

	def script_toggleX(self, gesture):
		char = gesture.mainKeyName[-1]
		if char == 'l':
			self.copy_line()
		elif char == 'k':
			self.copy_word()
		elif char == 'w':
			self.copy_window()
		tones.beep(700, 100)

	def copy_line(self):
		info = api.getReviewPosition().copy()
		info.expand(textInfos.UNIT_LINE)
		info.copyToClipboard()

	def copy_word(self):
		ui.message("word")
		info = api.getReviewPosition().copy()
		info.expand(textInfos.UNIT_WORD)
		info.copyToClipboard()

	def copy_window(self):
		info = api.getReviewPosition().copy()
		info.expand(textInfos.UNIT_STORY)
		t = info.clipboardText.rstrip('\n')
		api.copyToClip(t)

	def script_copy_to_start(self, gesture):
		info = api.getReviewPosition().copy()
		info2 = info.copy()
		info.expand(textInfos.UNIT_LINE)
		info.setEndPoint(info2, "endToEnd")
		info.copyToClipboard()
		ui.message("copied")

	def script_copy_to_end(self, gesture):
		info = api.getReviewPosition().copy()
		info2 = info.copy()
		info.expand(textInfos.UNIT_LINE)
		info.setEndPoint(info2, "startToStart")
		info.copyToClipboard()
		ui.message("copied")

	def script_virtualCopy(self, gesture):
		#If already toggling, send it on and clean up
		if self.toggling:
			gesture.send()
			return
		#alert the user of a gesture map error, rather than making the machine unusable
		try:
			self.bindGestures(self.__toggle_gestures)
		except:
			ui.message("Error binding copy gestures")
			raise
		self.toggling = True
		tones.beep(100, 10)
	script_virtualCopy.__doc__ = _("Copies things around the review cursor")
