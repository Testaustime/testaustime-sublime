import sublime
import sublime_plugin
import urllib
import json
import time
import os
import threading

PLUGIN_SETTINGS_KEY = "TestaustimeSettings"
API_SETTINGS_KEY = "testaustime_api_key"
ENDPOINT_SETTINGS_KEY = "testaustime_endpoint_url"

last_heartbeat = time.time()
can_show_missing_key_popup = True



class TestausTime:
    def __init__(self):
        self.settings = sublime.load_settings(PLUGIN_SETTINGS_KEY)
        if not self.get_endpoint_url():
        	print("no endpoint url defined, setting the value to https://api.testaustime.fi")
        	self.save_endpoint_url("https://api.testaustime.fi")
        if not self.get_api_key():
        	self.missing_api_key_popup()

    def missing_api_key_popup(self):
    	window = sublime.active_window()
    	global can_show_missing_key_popup
    	if can_show_missing_key_popup:
    		sublime.message_dialog("You haven't set the API key yet.\nSet it from 'Preferences -> testaustime -> Set API key")
    		can_show_missing_key_popup = False

    def save_api_key(self, api_key):
        self.settings.set(API_SETTINGS_KEY, api_key)
        sublime.save_settings(API_SETTINGS_KEY)

    def save_endpoint_url(self, endpoint_url):
    	self.settings.set(ENDPOINT_SETTINGS_KEY, endpoint_url)
    	sublime.save_settings(ENDPOINT_SETTINGS_KEY)

    def get_api_key(self):
        key = self.settings.get(API_SETTINGS_KEY, None)
        if key:
        	return str(key)

    def get_endpoint_url(self):
    	endpoint = self.settings.get(ENDPOINT_SETTINGS_KEY, None)
    	if endpoint:
    		return str(endpoint)

class prompt_api_key(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel("API key:", "", self._on_input_done, None, None)

    def _on_input_done(self, user_input):
        sublime.message_dialog("API key set")
        TestausTime().save_api_key(user_input)

	

class prompt_url_endpoint(sublime_plugin.WindowCommand):
	def run(self):
		self.window.show_input_panel("Endpoint URL:", "", self._on_input_done, None, None)

	def _on_input_done(self, user_input):
		sublime.message_dialog("Endpoint set")
		if not user_input.startswith("https://") and not user_input.startswith("http://"):
			user_input = "https://" + user_input
		if user_input.endswith("/"):
			user_input = user_input[:-1]
		TestausTime().save_endpoint_url(user_input)

class ApiCredHandler(sublime_plugin.TextCommand):
    def retrieve_api_key(self, edit):
        api_key = prompt_api_key()
        TestausTime.save_api_key(api_key)

class get_project_name(sublime_plugin.TextCommand):
	def run(self, edit):
		get_current_project_name()


class AsyncApiCall(threading.Thread):
	def __init__(self, timeout):
		threading.Thread.__init__(self)
	def run(self):
		threads = []
		err = ""

		try:
			if assemble_data() and assemble_headers():
				request = urllib.request.Request(TestausTime().get_endpoint_url() + '/activity/update', data=assemble_data(), headers=assemble_headers())
				response = urllib.request.urlopen(request)
				response_text = response.read().decode('utf-8')
				return response_text
		except (urllib.error.HTTPError) as e:
			err = '%s: HTTP error %s contacting API' % (__name__, str(e.code))
			print(err)
		except (urllib.error.URLError) as e:
		    err = '%s: URL error %s contacting API' % (__name__, str(e.reason))
		    print(err)
		self.result = False



"""
FUNCTIONS
"""

def get_current_syntax():
	view = sublime.active_window().active_view()
	syntax = view.settings().get('syntax')
	syntax = syntax.split('/')[-1].split('.')[0]
	return syntax

def show_project():
	view = sublime.active_window().active_view()
	if view.window() is None:
		return 'None'
	project_file = view.window ().project_file_name ()
	if project_file is not None:
		project_name = os.path.splitext (os.path.basename (project_file))[0]
		return project_name

def assemble_data():
	data = {
    'language': get_current_syntax(),
    'hostname': os.uname()[1],
    'editor_name': 'SublimeText',
    'project_name': str(show_project())
	}
	data = json.dumps(data).encode('utf-8')
	return data

def assemble_headers():
	if TestausTime().get_api_key():
		headers = {
	    'Content-Type': 'application/json',
	    'Authorization': 'Bearer ' + TestausTime().get_api_key(),
		}
		return(headers)


def get_user_data():
	request = urllib.request.Request((url + '/users/@me'), headers=assemble_headers())
	response = urllib.request.urlopen(request)
	response_text = response.read().decode('utf-8')
	print(response_text)

def heart_beat():
	thread = AsyncApiCall(5)
	thread.start()

def flush():
	"""placeholder"""
	print("Flush")

class IdleHandler(sublime_plugin.EventListener):
	def on_modified(view, event):
		global last_activity
		global last_heartbeat
		now = time.time()
		last_activity = now
		if now - last_heartbeat > 30:
			sublime.set_timeout_async(heart_beat(), 0)
			last_heartbeat = now
			
class get_user_data(sublime_plugin.TextCommand):
	pass
