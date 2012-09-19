"""Rivendell python module"""

from . import exc

import ConfigParser
import MySQLdb
import subprocess
import datetime
import re
import os

CONFIG_FILE = os.environ.get('RIVENDELL_CONFIG_FILE') or '/etc/rd.conf'
AUDIO_ROOT = os.environ.get('RIVENDELL_AUDIO_ROOT') or '/var/snd'

LOUDNESS_SINGLE_PATTERN = re.compile(r'^\s*(\-?\d+\.\d) LUFS, (\d{6}_\d{3})\.wav$', flags=re.MULTILINE)
LOUDNESS_GROUP_PATTERN = re.compile(r'^\s*(\-?\d+\.\d) LUFS$')




class Cart():
    def add_cut(self, cut):
        if isinstance(cut, Cut):
            self.cuts.append(cut)
        else:
            raise TypeError("Must supply Cut object")

    def get_loudness(self):
        paths = [cut.get_path() for cut in self.cuts]
        
        cuts_pattern = LOUDNESS_SINGLE_PATTERN
        cart_pattern = LOUDNESS_GROUP_PATTERN

        result = subprocess.check_output(['loudness', 'scan'] + paths)
        lines = result.splitlines()

        cuts_lufs = {cut[1][-3:]: float(cut[0]) for cut in cuts_pattern.findall(result)}
        cart_lufs = float(cart_pattern.search(lines[-1]).groups()[0])

        return (cart_lufs, cuts_lufs)

    def get_cuts(self):
        c = self._db.cursor()
        c.execute('SELECT cut_name, play_gain '
                  'FROM CUTS WHERE cart_number=%s ', (self.number,))

        for cut in c:
            cut_obj = Cut(self._db, cut[0], kwargs=cut)
            self.add_cut(cut_obj)

    def __init__(self, db, number, title=None, artist=None):
        self._db = db
        self.number = number
        self.title=title
        self.artist=artist

        self.cuts = []

    def __repr__(self):
        return 'Cart(%d)' % (self.number)

class Cut():
    def get_gain(self):
        c = self._db.cursor()
        c.execute('SELECT PLAY_GAIN FROM CUTS WHERE CUT_NAME=%s', (self.cut_name,))
        return c.fetchone()[0]

    def set_gain(self, gain):
        if not isinstance(gain, int):
            raise TypeError("Integer play gain value required.")
                                    
        c = self._db.cursor()
        c.execute('UPDATE CUTS SET PLAY_GAIN=%s WHERE CUT_NAME=%s; COMMIT;', (gain, self.cut_name))

    def amplify(self, gain):
        fail = re.compile(r'^sox FAIL .*?$', re.MULTILINE)
        warn = re.compile(r'^sox WARN .*?$', re.MULTILINE)
        path = self.get_path()
        result = subprocess.check_output(['sox', path, path+".tmp", 'gain', '{:+.3f}'.format(gain)], stderr=subprocess.STDOUT)

        if len(fail.findall(result)):
            print >>sys.stderr, "Errors were encountered :"
            print >>sys.stderr, "\n".join(fail.findall(result))

        if len(warn.findall(result)):
            print >>sys.stderr, "Warnings were encountered :"
            print >>sys.stderr, "\n".join(warn.findall(result))
            print >>sys.stderr, ("Not overwriting file. Please investigate.\n" +
                    "  new file: {0}.tmp\n  old file: {0}\n".format(path) )
        else:
            os.renames(path, os.path.dirname(path)+"/backups/"+os.path.basename(path))
            os.rename(path+".tmp", path)

    def get_loudness(self):
        album_pattern = LOUDNESS_GROUP_PATTERN
        
        with open('/dev/null', 'w') as devnull:
            result = subprocess.check_output(['loudness', 'scan', self.get_path()], stderr=devnull)

        if not result:
            raise exc.CutNotOnDisk(self.get_path()) if not os.path.isfile(self.get_path()) else exc.CutInvalid(self.cut_name)
        lastline = result.splitlines()[-1]

        return album_pattern.search(lastline).groups()[0]
         
    def get_path(self):
        return '/var/snd/' + os.path.basename('%s.wav' % (self.cut_name))

    def __init__(self, db, cut_name, **kwargs):
        self._db = db
        self.cut_name = cut_name
        self.values = kwargs

    def __repr__(self):
        return 'Cut(%s)' % (self.cut_name)

class CartRange():
    def __init__(self, db, from_number, to_number):
        self._db = db
        self.from_number = from_number
        self.to_number = to_number
        self.carts = []

        c = db.cursor()
        c.execute('SELECT number, title, artist '
                  'FROM CART WHERE number >= %s AND number <= %s', (from_number, to_number))

#        c.execute('SELECT CART.number, CART.artist, CART.title, '
#                  'CUTS.cut_name, CUTS.play_gain '
#                  'FROM CART JOIN CUTS ON CUTS.cart_number=CART.number ' 
#                  'WHERE CART.number >= %s AND CART.number <= %s ', (from_number,to_number))

        for result in c:
            cart = Cart(db, result[0], result[1], result[2])
            self.carts.append(cart)



        


class Host():
    def get_cart(self, number):
        cart = Cart(self._db, number)

        c = self._db.cursor()
        keys=['cart_number', 'cart_title', 'cart_artist','cut_name', 'cut_description','cut_play_gain'] 
        print "Got %s cuts." % (c.execute('SELECT CART.number, CART.title, CART.artist, '
                  'CUTS.cut_name, CUTS.description, CUTS.play_gain '
                  'FROM CART INNER JOIN CUTS on CART.number = CUTS.cart_number '
                  'WHERE CART.number = %s;', (number,)), )

        if not c.rowcount:
            raise exc.CartNotInDatabase(number) 
        else:
            for cut in c:
                cart.title, cart.artist = cut[1], cut[2]
                values = dict(zip(keys,cut))
                cut_obj = Cut(self._db, cut[3], kwargs=values)
                cart.add_cut(cut_obj)
            return cart
       
    def load_config(self, path=CONFIG_FILE):
        self.config = ConfigParser.RawConfigParser()
        try:
            if not path in self.config.read(path):
                raise RuntimeError('Config file "%s" does not exist' % (path) )
        except ConfigParser.Error as e:
            raise RuntimeError(e)
        self.mysql = {key:var for key, var in self.config.items('mySQL')}

    def connect_db(self):
        self._db = MySQLdb.connect(host=self.mysql['hostname'],
                                  port=3306,
                                  user=self.mysql['loginname'],
                                  passwd=self.mysql['password'],
                                  db=self.mysql['database'],
                                  )
        

    def log_exists(self, logname):
        c = self._db.cursor()
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

   

