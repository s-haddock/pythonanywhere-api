import requests, json
from bs4 import BeautifulSoup

class PythonAnywhere(object):
	def __init__(self):
		self.load_config()
		self.login_url = 'https://www.pythonanywhere.com/login/'
		self.logout_url	= 'https://www.pythonanywhere.com/logout/'
		self.files_url = 'https://www.pythonanywhere.com/user/{}/files/'.format(self.config['pythonanywhere']['username'])
		self.session = requests.Session()
		self.login()

	def load_config(self):
		with open('config.json') as data_file:    
			self.config = json.load(data_file)

	def get_csrf_token(self, url):
		r = self.session.get(url)
		soup = BeautifulSoup(r.content, 'lxml')
		return soup.find('input', attrs={'name':'csrfmiddlewaretoken'})['value']

	def set_headers(self, referer):
		self.headers = {
			'Referer': referer,
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 OPR/50.0.2762.67'
		}

	def login(self):
		self.set_headers(self.login_url)

		payload = {
			'csrfmiddlewaretoken': self.get_csrf_token(self.login_url),	
			'auth-username': self.config['pythonanywhere']['username'],
			'auth-password': self.config['pythonanywhere']['password'],
			'login_view-current_step': 'auth'
		}

		r = self.session.post(self.login_url, data=payload, headers=self.headers)
		r.raise_for_status()

	def logout(self):
		self.set_headers(self.logout_url)
		self.session.post(self.logout_url, headers=self.headers)

	def upload_file(self, local_path, server_path):
		url = self.files_url + server_path	
		self.set_headers(url)
		files = {'file': open(local_path, 'rb')}
		payload = {
			'csrfmiddlewaretoken': self.get_csrf_token(url)
		}

		r = self.session.post(url, data=payload, files=files, headers=self.headers)
		r.raise_for_status()

	def download_file(self, local_path, server_path):
		url = self.files_url + server_path
		self.set_headers(url)
		r = self.session.get(url)
		with open(local_path, 'wb') as data_file:
			data_file.write(r.content)
		r.raise_for_status()

	def delete_file(self, server_path):
		url = self.files_url + server_path	
		self.set_headers(url)
		payload = {
			'csrfmiddlewaretoken': self.get_csrf_token('/'.join(url.split('/')[:-1])),
			'action': 'delete_file'
		}
		r = self.session.post(url, data=payload, headers=self.headers)
		r.raise_for_status()

	def copy_file(self, current_path, future_path):
		current_url = self.files_url + current_path
		future_url = self.files_url + future_path
		self.set_headers(current_url)
		r = self.session.get(current_url)
		r.raise_for_status()

		files = {'file': (current_path.split('/')[-1], r.content, 'text/csv', {'Expires': '0'})}
		payload = {
			'csrfmiddlewaretoken': self.get_csrf_token(future_url)
		}
		self.set_headers(future_url)
		r = self.session.post(future_url, data=payload, files=files, headers=self.headers)
		r.raise_for_status()

	def list_dir(self, server_path):
		url = self.files_url + server_path
		self.set_headers(url)
		r = self.session.get(url)
		soup = BeautifulSoup(r.content, 'lxml')
		files = soup.findAll(attrs={'class':'filename'})
		if len(files) == 0:
			return []
		return [f.find('i')['title'] if f.find('i').has_attr('title') else f.find('a')['title'] for f in files]
