import sublime
import sublime_plugin
import sys
import os
import threading
import re
import time
import shutil

sys.path.append(os.getcwd() + os.sep + "fpconst")
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


def handle_missing_settings():
    sublime.error_message("Codechef: Ideone username or password isn't provided in Gist.sublime-settings file")
    if not os.path.exists(os.path.join(sublime.packages_path(), "User", "Codechef.sublime-settings")):
        shutil.copyfile(os.path.join(sublime.packages_path(), "Codechef", "Codechef.sublime-settings"), os.path.join(sublime.packages_path(), "User", "Codechef.sublime-settings"))
    sublime.active_window().open_file(os.path.join(sublime.packages_path(), "User", "Codechef.sublime-settings"))


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


class UnspecifiedCredentialsError(Exception):
    pass


class Ideone:
    def __init__(self, user='', password='', **kwargs):
        self._user = user
        self._password = password
        self.kwargs = kwargs
        if getProxySettings():
            self.kwargs['http_proxy'] = getProxySettings().replace('http://', '')
        if not self._user and not self._password:
            raise UnspecifiedCredentialsError

    def connect(self):
        self._wsdlObject = WSDL.Proxy('http://ideone.com/api/1/service.wsdl', **self.kwargs)

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
        if status < 0:
            status = -1
        return (status, result)

    def getSubmissionDetails(self, link, withSource=True, withInput=True, withOutput=True, withStderr=True, withCmpinfo=True):
        response = self._wsdlObject.getSubmissionDetails(self._user, self._password, link, withSource, withInput, withOutput, withStderr, withCmpinfo)
        error = getError(response)
        if error != "OK":
            raise Exception(error)
        details = response['item'][1:]
        return createDict(details)


class IdeoneLanguageThread(threading.Thread, Ideone):
    """docstring for IdeoneLanguageThread"""
    def __init__(self, user, password):
        threading.Thread.__init__(self)
        Ideone.__init__(self, user=user, password=password)
        self.result = False

    def run(self):
        self.connect()
        self.result = self.getLanguages()


class IdeoneResetLanguageSettingsCommand(sublime_plugin.ApplicationCommand):
    def run(self, args):
        self.language_list = sublime.load_settings("IdeoneLanguageList.sublime-settings")
        self.ideone_settings = sublime.load_settings("Codechef.sublime-settings")
        self.thread = IdeoneLanguageThread(user=str(self.ideone_settings.get('Ideone_user')), password=str(self.ideone_settings.get('Ideone_password')))
        self.thread.start()
        self.handle_thread()

    def handle_thread(self):
        if self.thread.is_alive():
            sublime.set_timeout((lambda: self.handle_thread()), 1000)
        else:
            if self.thread.result == False:
                return
            else:
                self.language_list.set("Languages", repr(self.thread.result))


class IdeoneSubmitThread(threading.Thread, Ideone):
    """docstring for IdeoneSubmitThread"""
    def __init__(self, user, password, code, language_id, input_text, whether_run=True, private=False):
        threading.Thread.__init__(self)
        Ideone.__init__(self, user=user, password=password)
        self.result = False
        self.code = code
        self.language_id = language_id
        self.input_text = input_text
        self.whether_run = whether_run
        self.private = private

    def run(self):
        self.connect()
        self.result = self.createSubmission(self.code, self.language_id, input=self.input_text, run=self.whether_run, private=self.private)


class IdeoneCheckOutputThread(threading.Thread, Ideone):
    """docstring for IdeoneCheckOutputThread"""

    def __init__(self, user, password, link, withSource=False, withInput=False, withOutput=True, withStderr=True, withCmpinfo=True):
        self.feedback = False
        self.result = False
        Ideone.__init__(self, user=user, password=password)
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
        self.result = self.getSubmissionDetails(self.link, self.withSource, self.withInput, self.withOutput, self.withStderr, self.withCmpinfo)


class IdeoneItCommand(sublime_plugin.TextCommand):
    def get_ideone_language(self):
        first_line = self.view.substr(self.view.line(0))
        m = re.match(r'.*?Ideone_Language_Id:.*?(\d+).*', first_line)
        if not m:
            self.view.set_status("SublimeCodechef", "You didn't specify the language in the first line. Click OK. We'll help you choose the language.")
            sublime.set_timeout(self.clear_status, 20000)
            if self.language_list.has("Languages"):
                self.languages = eval(self.language_list.get("Languages"))
                self.show_language_options()
            else:
                self.language_thread = IdeoneLanguageThread(user=str(self.ideone_settings.get('Ideone_user')), password=str(self.ideone_settings.get('Ideone_password')))
                self.language_thread.start()
                self.handle_language_thread()
            return
        return (m.group(1))

    def clear_status(self):
        self.view.set_status("SublimeCodechef", "")

    def handle_language_thread(self):
        if self.language_thread.is_alive():
            sublime.set_timeout((lambda: self.handle_language_thread()), 1000)
        else:
            if self.language_thread.result == False:
                sublime.error_message("Not able to load Languages list from Ideone. Check your Internet Connection!")
            else:
                self.languages = self.language_thread.result
                self.language_list.set("Languages", repr(self.language_thread.result))
                self.show_language_options()

    def show_language_options(self):
        self.view.window().show_quick_panel(self.languages.values(), self.set_language)

    def set_language(self, ind):
        if ind == -1:
            return
        selection = self.view.sel()
        selection_copy = []
        for s in selection:
            selection_copy.append(s)
        language_id = self.languages.keys()[ind]
        l = "Ideone_Language_Id:%d\n" % language_id
        e = self.view.begin_edit()
        self.view.insert(e, 0, l)
        self.view.end_edit(e)
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(0, 0))
        self.view.run_command("toggle_comment")
        self.view.sel().clear()
        for s in selection_copy:
            self.view.sel().add(sublime.Region(s.a + self.view.full_line(0).size(), s.b + self.view.full_line(0).size()))
        self.submit_to_ideone(language_id)

    def reset_edit(self):
        if self.edit:
            self.output_view.end_edit(self.edit)
        self.edit = self.output_view.begin_edit()

    def add_output(self, outp):
        self.reset_edit()
        self.output_view.insert(self.edit, self.output_view.size(), outp)
        self.output_view.show(self.output_view.size())

    def run(self, edit):
        self.edit = False
        self.title = "Ideone Output"
        self.language_list = sublime.load_settings("IdeoneLanguageList.sublime-settings")
        self.ideone_settings = sublime.load_settings("Codechef.sublime-settings")
        self.user = str(self.ideone_settings.get('Ideone_user'))
        self.password = str(self.ideone_settings.get('Ideone_password'))
        language_id = self.get_ideone_language()
        if not language_id:
            return
        self.submit_to_ideone(language_id)

    def submit_to_ideone(self, language_id):
        code = self.view.substr(sublime.Region(0, self.view.size()))
        self.file_name = self.view.file_name()
        self.input_file_name = re.sub(r'(.*)\..*', r'\1.txt', self.file_name)
        input_text = ''
        if os.path.exists(self.input_file_name):
            with open(self.input_file_name) as ifn:
                input_text = ifn.read()
        try:
            self.thread = IdeoneSubmitThread(self.user, self.password, code, language_id, input_text)
        except UnspecifiedCredentialsError:
            handle_missing_settings()
            return
        self.thread.start()
        f = filter(lambda v: v.name() == self.title, self.view.window().views())
        self.output_view = f[0] if len(f) else self.view.window().new_file()
        self.output_view.set_name(self.title)
        self.output_view.set_scratch(True)
        self.output_view.show(self.output_view.size())
        self.output_view.set_read_only(False)
        self.reset_edit()
        self.reset_edit()
        try:
            self.view.window().focus_view(self.output_view)
        except:
            pass
        self.add_output("\n\nSubmitting " +
            os.path.basename(os.path.normpath(self.file_name)) +
            (" and " + os.path.basename(os.path.normpath(self.input_file_name)) if input_text else "") +
            " to Ideone...\n")
        self.handle_thread()

    def handle_thread(self):
        if self.thread.is_alive():
            self.add_output("Still trying to submit...\n")
            sublime.set_timeout((lambda: self.handle_thread()), 1000)
        else:
            if self.thread.result == False:
                self.add_output("Failed, please try again\n")
                return
            else:
                self.add_output("Submit successful. your code is at : http://ideone.com/" + self.thread.result + "\n")
                self.add_output("Running...\n")
                self.check_output_thread = IdeoneCheckOutputThread(self.user, self.password, self.thread.result)
                self.check_output_thread.start()

                self.handle_check_output_thread()

    def handle_check_output_thread(self):
        if self.check_output_thread.is_alive():
            self.add_output("Still running...\n")
            sublime.set_timeout((lambda: self.handle_check_output_thread()), 1000)
        else:
            if self.check_output_thread.result == False:
                self.add_output("Failed, please try again\n")
                return
            else:
                res = "\nResult: With " + \
                self.check_output_thread.result['langVersion'] + \
                "\nCompiler Info starts at next line: ##################################\n" + \
                self.check_output_thread.result['cmpinfo'] + \
                "\nStderr starts at next line: #########################################\n" +\
                self.check_output_thread.result['stderr'] + \
                "\nAnd Output starts with next line: ###################################\n" +\
                self.check_output_thread.result['output']
                self.add_output((res))
                self.view.end_edit(self.edit)
                self.edit = False
