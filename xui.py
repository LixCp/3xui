import requests, pickle, os, uuid, string, random, json
import urllib3
urllib3.disable_warnings()

class xui:

    def __init__(self, address, username, password, port = 54321, ssl = False):
        self.address = address
        self.username = username
        self.password = password
        self.port = port
        self.ssl = ssl
        if ssl:
            self.url = f'https://{self.address}:{self.port}'
        else :
            self.url = f'http://{self.address}:{self.port}'
        self.cookie = f'cookies/{self.address}:{self.port}.txt'

    def check(self):
        try:
            requests.get(self.url)
            return True
        except (requests.exceptions.ConnectionError):
            return False
            
    def login(self):
        if(self.check):
            if os.path.exists(self.cookie):
                os.unlink(self.cookie)
            data = {'username': self.username, 'password': self.password,'LoginSecret': ''}
            if self.ssl:
                r = requests.post(f"{self.url}/login", data=data)
            else :
                r = requests.post(f"{self.url}/login", data=data, verify=False)
            self.save_cookies(r.cookies, self.cookie)
            print(r.text)
            return r.json()
        else:
            return {'success' : False}
        
    def status(self):
        if(self.check):
            if self.ssl:
                r = requests.post(f"{self.url}/server/status", cookies = self.load_cookies(self.cookie))
            else :
                r = requests.post(f"{self.url}/server/status", cookies = self.load_cookies(self.cookie), verify=False)
            return r.json()
        else:
            return {'success' : False}
    
    def logout(self):
        if(self.check):
            if self.ssl:
                r = requests.post(f"{self.url}/logout", cookies = self.load_cookies(self.cookie))
            else :
                r = requests.post(f"{self.url}/logout", cookies = self.load_cookies(self.cookie), verify=False)
            os.unlink(self.cookie)
            return True
        else:
            return {'success' : False}
        
    def addClient(self,id ,expiryTime, total, limitIp = 0):
        if(self.check):
            xuid = str(uuid.uuid4())
            email = self.get_random_string(9)
            data = {
                'id' : id,
                'settings' : json.dumps({
                    "clients": [
                        {
                            "id": xuid,
                            "flow": "",
                            "email": email,
                            "limitIp": limitIp,
                            "totalGB": int(total) * (1024**3),
                            "expiryTime": int(round(float(expiryTime))) * 1000,
                            "enable": True,
                            "tgId": "",
                            "subId": self.get_random_string(14)
                        }
                    ]
                })
            }
            if self.ssl:
                r = requests.post(f"{self.url}/panel/inbound/addClient", data=data, cookies = self.load_cookies(self.cookie))
            else :
                r = requests.post(f"{self.url}/panel/inbound/addClient", data=data, cookies = self.load_cookies(self.cookie), verify=False)
            cccc = r.json()
            print(r)
            print(r.text)
            cccc['obj'] = {}
            cccc['obj']['uuid'] = xuid
            cccc['obj']['email'] = email
            return cccc
        else:
            return {'success' : False}

    def addInbound(self, remark, expiryTime, total, limitIp = 0):
        if(self.check):
            xuid = str(uuid.uuid4())
            email = self.get_random_string(9)
            data = {
                'up' : 0,
                'down' : 0,
                'total' : int(total) * (1024**3),
                'enable' : True,
                'listen' : '',
                'remark': remark, 
                'expiryTime': int(round(float(expiryTime))) * 1000, 
                'port': random.randint(11111,99999), 
                'protocol': 'vless',
                'settings' : json.dumps({
                    'clients' : [
                        {
                            'id' : xuid,
                            'flow' : '',
                            'email' : email,
                            'limitIp' : limitIp,
                            'totalGB' : 0,
                            'expiryTime' : 0,
                            'enable' : True,
                            'tgId' : '',
                            'subId' : self.get_random_string(14)
                        }
                    ],
                    'decryption' : 'none',
                    'fallbacks' : []
                }),
                'streamSettings' : json.dumps({
                    'network' : 'ws',
                    'security' : 'none',
                    'wsSettings' : {
                        'acceptProxyProtocol' : False,
                        'path' : '/',
                        'headers' : {}
                    }
                }),
                'sniffing' : json.dumps({
                    'enabled' : True,
                    'destOverride' : [
                        'http'
                    ]
                })
            }
            if self.ssl:
                r = requests.post(f"{self.url}/panel/inbound/addClient", data=data, cookies = self.load_cookies(self.cookie))
            else :
                r = requests.post(f"{self.url}/panel/inbound/addClient", data=data, cookies = self.load_cookies(self.cookie), verify=False)
            cccc = r.json()
            cccc['obj']['uuid'] = xuid
            cccc['obj']['email'] = email
            return cccc
        else:
            return {'success' : False}
        
    def delInbound(self, id):
        if(self.check):
            r = requests.post(f'{self.url}/panel/inbound/del/{id}', cookies = self.load_cookies(self.cookie), verify=False)
            return r.json()
        else:
            return {'success' : False}
    
    def save_cookies(self, requests_cookiejar, filename):
        with open(filename, 'wb') as f:
            pickle.dump(requests_cookiejar, f)
    
    def load_cookies(self, filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
        
    def get_random_string(self, length):
        letters = string.ascii_lowercase
        result_str = ''.join(random.choice(letters) for i in range(length))
        return result_str