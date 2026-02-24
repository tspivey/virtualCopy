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

def _trim_lines(text):
	return "\r\n".join(line.strip() for line in text.splitlines())

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
			self.__toggle_gestures["KB:shift+%s" % c] = "toggleX"
			self.__toggle_gestures["KB:NVDA+shift+%s" % c] = "toggleX"
		#home and end
		self.__toggle_gestures["KB:home"] = "copy_to_start"
		self.__toggle_gestures["KB:end"] = "copy_to_end"
		self.__toggle_gestures["KB:shift+home"] = "copy_to_start_trimmed"
		self.__toggle_gestures["KB:shift+end"] = "copy_to_end_trimmed"
		#block copy
		self.__toggle_gestures["KB:b"] = "copy_block"
		self.__toggle_gestures["KB:NVDA+b"] = "copy_block"
		self.__toggle_gestures["KB:shift+b"] = "copy_block_trimmed"
		self.__toggle_gestures["KB:NVDA+shift+b"] = "copy_block_trimmed"

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
		trimmed = "shift" in gesture.modifierNames
		if char == 'l':
			self.copy_line(trimmed)
		elif char == 'k':
			self.copy_word(trimmed)
		elif char == 'w':
			self.copy_window(trimmed)
		tones.beep(700, 100)

	def copy_line(self, trimmed=False):
		info = api.getReviewPosition().copy()
		info.expand(textInfos.UNIT_LINE)
		if trimmed:
			api.copyToClip(_trim_lines(info.clipboardText))
		else:
			info.copyToClipboard()

	def copy_word(self, trimmed=False):
		info = api.getReviewPosition().copy()
		info.expand(textInfos.UNIT_WORD)
		if trimmed:
			api.copyToClip(_trim_lines(info.clipboardText))
		else:
			info.copyToClipboard()

	def copy_window(self, trimmed=False):
		info = api.getReviewPosition().copy()
		info.expand(textInfos.UNIT_STORY)
		t = info.clipboardText.rstrip('\n')
		if trimmed:
			t = _trim_lines(t)
		api.copyToClip(t)

	def script_copy_to_start(self, gesture, trimmed=False):
		info = api.getReviewPosition().copy()
		info2 = info.copy()
		info.expand(textInfos.UNIT_LINE)
		info.setEndPoint(info2, "endToEnd")
		if trimmed:
			api.copyToClip(_trim_lines(info.clipboardText))
		else:
			info.copyToClipboard()
		ui.message("copied")

	def script_copy_to_end(self, gesture, trimmed=False):
		info = api.getReviewPosition().copy()
		info2 = info.copy()
		info.expand(textInfos.UNIT_LINE)
		info.setEndPoint(info2, "startToStart")
		if trimmed:
			api.copyToClip(_trim_lines(info.clipboardText))
		else:
			info.copyToClipboard()
		ui.message("copied")

	def script_copy_to_start_trimmed(self, gesture):
		self.script_copy_to_start(gesture, trimmed=True)

	def script_copy_to_end_trimmed(self, gesture):
		self.script_copy_to_end(gesture, trimmed=True)

	def _copy_block(self, trimmed=False):
		pos = api.getReviewPosition().copy()
		startMarker = getattr(pos.obj, "_copyStartMarker", None)
		if not startMarker:
			# Translators: message when no start marker has been set
			ui.message(_("No start marker"))
			tones.beep(120, 100)
			return
		if startMarker.compareEndPoints(pos, "startToStart") > 0:
			startMarker, pos = pos, startMarker
		startMarker.setEndPoint(pos, "endToEnd")
		t = startMarker.clipboardText
		if trimmed:
			t = _trim_lines(t)
		api.copyToClip(t)
		tones.beep(700, 100)

	def script_copy_block(self, gesture):
		self._copy_block(trimmed=False)

	def script_copy_block_trimmed(self, gesture):
		self._copy_block(trimmed=True)

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
