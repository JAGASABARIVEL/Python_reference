import logging

from logging import Formatter as Formatter
from logging import StreamHandler as StreamHandler
from logging import FileHandler as FileHandler

from logging.handlers import RotatingFileHandler as RotatingFileHandler

import inspect

class logger(Formatter,
	     StreamHandler,
	     FileHandler,
	     RotatingFileHandler):

	def __init__(self, loggerName=None):
		self.ListLoggers = {}
		self.ListFormatters = {}
		self.ListHandlers = {}
		self.logger_ = None
		self.filename = '/root/Jaga/Control_Plane/TestRepo/aurora_cdvr_sanity_tests/scripts/basic_feature_scripts_ppsv3/logging.log'
		self.mode = 'a'
		self.loggerName = loggerName
		
	def _initLogger(self, loggerName=None):
		self.logger = logging.getLogger('production.cdvr.scripts.basicfeatures.%s'% (__name__))
		self.ListLoggers.update({ 'logger' : { 'D' : self.logger }})
		
	def _initFormatter(self):
		self.DEFAULT = Formatter('%(asctime)s %(levelname)s %(name)s.%(modulename)s.%(functionname)s %(message)s')
		self.ListFormatters.update({'default' : {'D' : self.DEFAULT}})

	def _initHandler(self):
		self.SH_1 = StreamHandler()
		self.SH_1.setLevel(logging.DEBUG)
		
		self.ListHandlers.update({'stream' : {'D' : [self.SH_1] }})
		
		self.FH_1 = FileHandler(self.filename,self.mode)
		self.FH_1.setLevel(logging.DEBUG)
		self.ListHandlers.update({'file' : { 'D' : [self.FH_1] }})
		
		self.RH = RotatingFileHandler(self.filename, mode='a', maxBytes=1024*5, backupCount=10)
		self.ListHandlers.update({'logrotate' : { 'D' : [self.RH] }})
		
	def buildLogger(self,request):
		self._initLogger()
		self._initFormatter()
		self._initHandler()
		if request == 'DEVELOPER':
			self.logger_ = [ self.ListLoggers[logger] for logger in self.ListLoggers.keys() ][0]['D']
			
			self.logger_.setLevel(logging.DEBUG)
			if not self.logger_.handlers:
				self.format_ = [ self.ListFormatters[format] for format in self.ListFormatters.keys() if format == 'default' ][0]['D']


				self.streamhandler_ = [ self.ListHandlers[handler] for handler in self.ListHandlers.keys() if handler == 'stream' ][0]['D'][0]
				self.filehandler_ = [ self.ListHandlers[handler] for handler in self.ListHandlers.keys() if handler == 'file' ][0]['D'][0]
				self.rotatehandler_ = [ self.ListHandlers[handler] for handler in self.ListHandlers.keys() if handler == 'logrotate' ][0]['D'][0]
	
				self.streamhandler_.setFormatter(self.format_)
				self.filehandler_.setFormatter(self.format_)
		
				self.logger_.addHandler(self.streamhandler_)
				self.logger_.addHandler(self.filehandler_)
				self.logger_.addHandler(self.rotatehandler_)
				
				self.logger_ = self.logger_
			else:
				self.logger_ = self.logger_
			
		elif request == 'PRODUCTION':
			self.logger_ = [ self.ListLoggers[logger] for logger in self.ListLoggers.keys() ][0]['P']

                        self.logger_.setLevel(logging.DEBUG)
			if not self.logger_.handlers:
                        	self.format_ = [ self.ListFormatters[format] for format in self.ListFormatters.keys() if format == 'default' ][0]['P']


                        	self.streamhandler_ = [ self.ListHandlers[handler] for handler in self.ListHandlers.keys() if handler == 'stream' ][0]['P'][0]
                        	self.filehandler_ = [ self.ListHandlers[handler] for handler in self.ListHandlers.keys() if handler == 'file' ][0]['P'][0]
                        	self.rotatehandler_ = [ self.ListHandlers[handler] for handler in self.ListHandlers.keys() if handler == 'logrotate' ][0]['P'][0]
	
	                        self.streamhandler_.setFormatter(self.format_)
	                        self.filehandler_.setFormatter(self.format_)

	                        self.logger_.addHandler(self.streamhandler_)
	                        self.logger_.addHandler(self.filehandler_)
	                        #self.logger_.addHandler(self.rotatehandler_)

	                        self.logger_ = self.logger_
			else:
				self.logger_ = self.logger_

	def info(self,message):
                currentframe = inspect.currentframe()
                functionname = inspect.getouterframes(currentframe)[1][3]
                modulename = inspect.getouterframes(currentframe)[1][1]
                self.logger_.info('%s',message, extra={ 'functionname' : functionname, 'modulename' : modulename })

	def debug(self,message):
                currentframe = inspect.currentframe()
                functionname = inspect.getouterframes(currentframe)[1][3]
                modulename = inspect.getouterframes(currentframe)[1][1]
                self.logger_.debug('%s',message, extra={ 'functionname' : functionname, 'modulename' : modulename })	
		#logging.debug('Hello')

	def error(self,message):
		currentframe = inspect.currentframe()
		functionname = inspect.getouterframes(currentframe)[1][3]
		modulename = inspect.getouterframes(currentframe)[1][1]
		self.logger_.error('%s',message, extra={ 'functionname' : functionname, 'modulename' : modulename })
	
	def critical(self,message):
                currentframe = inspect.currentframe()
                functionname = inspect.getouterframes(currentframe)[1][3]
                modulename = inspect.getouterframes(currentframe)[1][1]
                self.logger_.critical('%s',message, extra={ 'functionname' : functionname, 'modulename' : modulename })

