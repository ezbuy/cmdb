import requests
import json
import yaml
from mico.settings import salt_api_url,salt_user,salt_password,salt_api_url2,salt_location

class SaltApi(object):
    def __init__(self,location='local'):
        print '------location:',location
        if location == salt_location:
            self.__loginUrl = salt_api_url2 + '/login'
            self.__url = salt_api_url2
        else:
            self.__loginUrl = salt_api_url + '/login'
            self.__url = salt_api_url
        self.__username = salt_user
        self.__password = salt_password



    def salt_login(self):
        params = {'eauth': 'pam',
                  'username': self.__username,
                  'password': self.__password
                  }
        headers = {'Accept': 'application/json'}
        obj = requests.post(self.__loginUrl,headers=headers,data=params,verify=False).content
        data = json.loads(obj)
        token = data['return'][0]['token']
        return token

    def salt_cmd(self,data):
        self.data = data
        self.__token_id = self.salt_login()
        headers = {'Accept': 'application/x-yaml',
                   'X-Auth-Token': '%s' % self.__token_id
                   }
        obj = requests.post(self.__url,headers=headers,data=self.data,verify=False)
        print 'salt_cmd---obj : '
        print obj
        obj = obj.content
        print 'salt_cmd---obj.content : '
        print obj
        try:
            print 'salt_cmd---yaml.load(obj) : '
            print yaml.load(obj)
            return yaml.load(obj)
        except Exception, e:
            print 'salt_cmd---Exception : '
            print e
            return 0
