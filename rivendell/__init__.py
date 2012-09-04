"""Rivendell python module"""

import ConfigParser
import MySQLdb
import subprocess
import datetime
import os

CONFIG_FILE = os.environ.get('RIVENDELL_CONFIG_FILE') or '/etc/rd.conf'

class LogExists(Exception):
    """Log already exists"""
    pass


class Rivendell():
    def load_config(self, path=CONFIG_FILE):
        self.config = ConfigParser.RawConfigParser()
        try:
            if not path in self.config.read(path):
                raise RuntimeError('Config file "%s" does not exist' % (path) )
        except ConfigParser.Error as e:
            raise RuntimeError(e)
        self.mysql = {key:var for key, var in self.config.items('mySQL')}

    def connect_db(self):
        self.db = MySQLdb.connect(host=self.mysql['hostname'],
                                  port=3306,
                                  user=self.mysql['loginname'],
                                  passwd=self.mysql['password'],
                                  db=self.mysql['database'],
                                  )
        

    def log_exists(self, logname):
        c = self.db.cursor()
        return True if c.execute('SHOW TABLES LIKE %s', (logname+'_LOG',)) else False

    def generate_tomorrow(self, service):
        if not isinstance(service, str):
            raise TypeError("'service' must be a string!")

        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        t_str = tomorrow.strftime('%Y_%m_%d')

        if not self.log_exists(t_str):
            subprocess.call(['rdlogmanager', '-g', '-s', service, '-d', '1'])
            return t_str
        else:
            raise LogExists("Log '%s' exists" % t_str)
        
    def __init__(self):
        self.load_config()
        self.connect_db()
