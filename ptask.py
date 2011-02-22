#!/usr/bin/python
# -*- coding: utf-8 -*-

import cmd
import getpass
import random
import sqlite3
import hashlib

INTRO = [
    'Welcome to ptask', 
    'Type "help" to get a list of available commands.',
]

# FIXME: Esto no va aquí, debemos establecer la conexión al momento de autenticar al usuario
#conn = sqlite3.connect('ptask.db')
#c = conn.cursor()

class Ptask(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = 'ptask> '
        self.intro = '\n'.join(INTRO)
        initdb()
        self.cmdloop()

    def do_inituser(self, line):
        #user_name, password
        name = raw_input('user_name: ')
        pwd = getpass.getpass("password: ")
        repwd = getpass.getpass("password again: ")
        if pwd == repwd:
           create_user(name,pwd)
        else:
           print 'Password mismatch!'

    def do_help(self, line):
        print "this is da help"
    
    def default(self, line):
        print '\n'.join(['Command not found.', INTRO[1]])


    #class functions

    def salt(self):
        s = ""
        for i in range(7):
            s = s + chr(random.randrange(65,128))        
        return s

    def create_user(self, name, pwd):
        m = hashlib.md5()
        salt = self.salt()
        m.update(password + self.salt())
        password = m.hexdigest()
        if self.c:
           self.c.execute('INSERT INTO users VALUES (0, ?,?,?,null)', name, password, salt)
           self.c.commit()

    
    def initdb(self):
        conn = sqlite3.connect('ptask.db')
        self.c = conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXIST taskrecords  (id INTEGER PRIMARY KEY, user_id INTEGER, description TEXT, task TEXT, start_date DATE, end_date DATE, estimated_time INTEGER, worked_timed INTEGER, tags TEXT)''') 
        self.c.execute('''CREATE TABLE IF NOT EXIST users  (id INTEGER PRIMARY KEY, realname TEXT, password_hash TEXT, password_salt TEXT, last_login DATE) ''')
        self.c.commit()
        
if __name__ == '__main__':
    p = Ptask()
