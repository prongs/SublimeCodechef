# Ideone_Language_Id: 4
import sublime, sublime_plugin
import sys,os,threading,re,time

sys.path.append(os.getcwd()+os.sep+"fpconst")
from SOAPpy import WSDL

RESPONSE_OK = "OK"

class Status:
	Waiting = -1
	Done = 0
	Compiling = 1
	Running = 3

class Result:
	NotRunning = 0
	CompileError = 11
	RuntimeError = 12
	Timeout = 13
	Success = 15
	MemoryLimit = 17
	IllegalSystemCall = 19
	InternalError = 20


def createTuple(item):
	return (item['key'], item['value']) 

def createDict(items):
	dict = {}
	for item in items:
		key = item['key']
		value = item['value']
		dict[key] = value
	return dict

def getError(response):
	if response['item'][0] == 'error':
		return response['item']['value']
	else:
		return response['item'][0]['value']


def getProxySettings():
	return os.environ.get('http_proxy')

class Ideone:
	def __init__(self, user='test', password='test',**kwargs):
		self._user = user
		self._password = password
		self.kwargs=kwargs
		self.kwargs['http_proxy']=getProxySettings().replace('http://','')
	def connect(self):
		self._wsdlObject = WSDL.Proxy('http://ideone.com/api/1/service.wsdl',**self.kwargs)

	def testFunction(self):
		response = self._wsdlObject.testFunction(self._user, self._password)
		error = getError(response)
		if error != "OK": 
			raise Exception(error)
		items = response['item']
		dict = createDict(items)
		return dict

	def getLanguages(self):
		response = self._wsdlObject.getLanguages(self._user, self._password)
		error = getError(response)
		if error != "OK": 
			raise Exception(error)
		languages = response['item'][1]['value']['item']
		dict = createDict(languages)
		return dict

	def createSubmission(self, code, language, input='', run=True, private=True):
		response = self._wsdlObject.createSubmission(self._user, self._password, code, language, input, run, private)
		error = getError(response)
		if error != "OK": 
			raise Exception(error)
		link = response['item'][1]['value']
		return link

	def getSubmissionStatus(self, link):
		response = self._wsdlObject.getSubmissionStatus(self._user, self._password, link)
		error = getError(response)
		if error != "OK": 
			raise Exception(error)
		status = response['item'][1]['value']
		result = response['item'][2]['value']
		if status < 0: status = -1
		return (status, result)

	def getSubmissionDetails(self, link, withSource=True, withInput=True, withOutput=True, withStderr=True, withCmpinfo=True):
		response = self._wsdlObject.getSubmissionDetails(self._user, self._password, link, withSource, withInput, withOutput, withStderr, withCmpinfo)
		error = getError(response)
		if error != "OK": 
			raise Exception(error)
		details = response['item'][1:]
		return createDict(details)

	def getLanguages(self):
		response = self._wsdlObject.getLanguages(self._user, self._password)
		error=getError(response)
		if error!= "OK":
			raise Exception(error)
		return createDict(response['item'][1][1][0])
		
		
class IdeoneLanguageThread(threading.Thread, Ideone):
	"""docstring for IdeoneLanguageThread"""
	def __init__(self, user,password):
		threading.Thread.__init__(self)
		Ideone.__init__(self,user=user,password=password)
		self.result=False
	def run(self):
		self.connect()
		self.result=self.getLanguages()		
		
class IdeoneResetLanguageSettingsCommand(sublime_plugin.TextCommand):
	def run(self,edit):		
		self.language_list= sublime.load_settings("IdeoneLanguageList.sublime-settings")
		self.ideone_settings = sublime.load_settings("SublimeCodechef.sublime-settings")
		self.thread=IdeoneLanguageThread(user=str(self.ideone_settings.get('Ideone_user')), password=str(self.ideone_settings.get('Ideone_password')));
		self.thread.start()
		self.handle_thread()
	def handle_thread(self):
		if self.thread.is_alive():
			sublime.set_timeout((lambda : self.handle_thread()), 1000)
		else:
			if self.thread.result==False:
				return
			else:
				for key in sorted(self.thread.result.keys()):
					self.language_list.set(str(key),self.thread.result[key])
				sublime.save_settings('IdeoneLanguageList.sublime-settings')

class IdeoneSubmitThread(threading.Thread, Ideone):
	"""docstring for IdeoneSubmitThread"""
	def __init__(self, user,password,code,language_id,input_text,whether_run=True,private=False):
		threading.Thread.__init__(self)
		Ideone.__init__(self,user=user,password=password)
		self.result=False
		self.code=code
		self.language_id=language_id
		self.input_text=input_text
		self.whether_run=whether_run
		self.private=private
	def run(self):
		self.connect()
		self.result=self.createSubmission(self.code, self.language_id, input=self.input_text, run=self.whether_run, private=self.private)


class IdeoneCheckOutputThread(threading.Thread, Ideone):
	"""docstring for IdeoneCheckOutputThread"""
	def __init__(self, user,password,link, withSource=False, withInput=False, withOutput=True, withStderr=True, withCmpinfo=True):
		self.feedback=False
		self.result=False
		Ideone.__init__(self,user=user,password=password)
		threading.Thread.__init__(self)		
		self.link = link
		self.withSource = withSource
		self.withInput = withInput
		self.withOutput = withOutput
		self.withStderr = withStderr
		self.withCmpinfo = withCmpinfo
	def run(self):
		self.connect()
		while self.getSubmissionStatus(self.link)[0] != Status.Done:
			time.sleep(1)
		self.result=self.getSubmissionDetails(self.link, self.withSource, self.withInput, self.withOutput, self.withStderr, self.withCmpinfo)
		

class IdeoneItCommand(sublime_plugin.TextCommand):
	def get_ideone_language(self):
		first_line=self.view.substr(self.view.line(0))
		m=re.match(r'.*?Ideone_Language_Id:.*?(\d+).*', first_line)
		if not m:
			self.view.set_status('SublimeCodechef',"First line doesn't specify the language")
			return None		
		self.view.set_status('SublimeCodechef',"")
		return (m.group(1))
	def run(self, edit):
		self.title="Ideone Output"
		self.ideone_settings = sublime.load_settings("SublimeCodechef.sublime-settings")
		self.user=str(self.ideone_settings.get('Ideone_user'))
		self.password=str(self.ideone_settings.get('Ideone_password'))
		language_id=self.get_ideone_language()
		if not language_id:
			return
		code=self.view.substr(sublime.Region(0,self.view.size()))
		self.file_name=self.view.file_name()
		self.input_file_name=re.sub(r'(.*)\..*',r'\1.txt',self.file_name)
		input_text=''
		if os.path.exists(self.input_file_name):
			with open(self.input_file_name) as ifn:
				input_text=ifn.read()
		self.thread=IdeoneSubmitThread(self.user,self.password,code,language_id,input_text)
		self.thread.start()
		f=filter(lambda v: v.name()==self.title, self.view.window().views())
		self.output_view=f[0] if len(f) else self.view.window().new_file()
		self.output_view.set_name(self.title)
		self.output_view.set_scratch(True)
		self.output_view.show(self.output_view.size())
		self.output_view.set_read_only(False)
		self.edit=self.output_view.begin_edit()
		try:
			self.view.window().focus_view(self.output_view)
		except:
			pass
		self.output_view.insert(self.edit, self.output_view.size(), "\n\nSubmitting "+
			os.path.basename(os.path.normpath(self.file_name))+
			(" and "+os.path.basename(os.path.normpath(self.input_file_name)) if input_text else "")+
			" to Ideone...\n")
		self.handle_thread()
	def handle_thread(self):
		if self.thread.is_alive():
			self.output_view.insert(self.edit,self.output_view.size(), "Still trying to submit...\n")
			sublime.set_timeout((lambda : self.handle_thread()), 1000)
		else:
			if self.thread.result==False:
				self.output_view.insert(self.edit,self.output_view.size(), "Failed, please try again\n")
				return
			else:
				self.output_view.insert(self.edit,self.output_view.size(), "Submit successful. your code is at : http://ideone.com/"+self.thread.result+"\n")
				self.output_view.insert(self.edit,self.output_view.size(), "Running...\n")
				self.check_output_thread=IdeoneCheckOutputThread(self.user, self.password,self.thread.result)
				self.check_output_thread.start()
				self.handle_check_output_thread()
	def handle_check_output_thread(self):
		if self.check_output_thread.is_alive():
			self.output_view.insert(self.edit,self.output_view.size(), "Still running...\n")
			sublime.set_timeout((lambda : self.handle_check_output_thread()), 1000)
		else:
			if self.check_output_thread.result==False:
				self.output_view.insert(self.edit,self.output_view.size(), "Failed, please try again\n")
				return
			else:
				print self.check_output_thread.result
				res="\nResult: With "+\
				self.check_output_thread.result['langVersion']+\
				 "Compiler Info starts at next line:\n"+\
				self.check_output_thread.result['cmpinfo']+\
				"\nStderr starts at next line:\n"+self.check_output_thread.result['stderr']+\
				"\nAnd Output starts with next line:\n"+self.check_output_thread.result['output']+"\n"
				self.output_view.insert(self.edit,self.output_view.size(), (res)+"\n")
