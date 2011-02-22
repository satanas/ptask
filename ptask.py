#!/usr/bin/python
# -*- coding: utf-8 -*-

import cmd
import getpass
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
        self.cmdloop()

    def do_inituser(self, line):
        #user_name, password
        name = raw_input('user_name: ')
        pwd = getpass.getpass("password: ")
	repwd = getpass.getpass("password again: ")
        if pwd == repwd:
           m = hashlib.md5()
           m.update(pwd)
           self.user_name = name
           self.user_pwd = m.hexdigest()
           

    def do_help(self, line):
        print "this is da help"
    
    def default(self, line):
        print '\n'.join(['Command not found.', INTRO[1]])

    def initdb(self, user_name, user_pwd, user_pwd_salt):
        conn = sqlite3.connect('ptask.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXIST taskrecords  (id INTEGER PRIMARY KEY, user_id INTEGER, description TEXT, task TEXT, start_date DATE, end_date DATE, estimated_time INTEGER, worked_timed INTEGER, tags TEXT)''') 
        c.execute('''CREATE TABLE IF NOT EXIST users  (id INTEGER PRIMARY KEY, realname TEXT, password_hash TEXT, password_salt TEXT, last_login DATE) ''')
        c.commit()
        c.execute('INSERT INTO users VALUES (0,?,?,?,null)', user_name, user_pwd, user_pwd_salt)
        
if __name__ == '__main__':
    p = Ptask()
