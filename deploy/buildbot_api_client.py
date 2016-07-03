import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Hack to remove a lot of warnings in stdout while testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class BuildbotDataAPi():
    def __init__(self, base_url, login, password):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
        }
        self.auth = HTTPBasicAuth(login, password)

    def post(self, route, method, params={}):
        data = {
            'id': 1,
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }
        res = requests.post(self.base_url + route, json=data,
                            headers=self.headers,
                            auth=self.auth)
        print res.json()
        res.raise_for_status()
        return res.json()

    def get(self, route):
        res = requests.get(self.base_url + route, headers=self.headers)
        res.raise_for_status()
        return res.json()

    def get_element_id_from_name(self, route, name, id_key, name_key='name'):
        elements = self.get(route)[route]
        for e in elements:
            if e[name_key] == name:
                _id = e[id_key]
                break
        else:
            raise Exception('element not found')
        return _id

    def force_build(self, builderid):
        params = {
            'builderid': str(builderid),
            'username': '',
            'reason': 'force build',
            'repository': '',
            'project': '',
            'branch': '',
            'revision': ''
        }
        self.post('forceschedulers/force-bootstrap', 'force', params=params)
