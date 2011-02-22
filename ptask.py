#!/usr/bin/python
# -*- coding: utf-8 -*-

import cmd
import sqlite3

INTRO = [
    'Welcome to ptask', 
    'Type "help" to get a list of available commands.',
]

conn = sqlite3.connect('ptask.db')
c = conn.cursor()

class Ptask(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = 'ptask> '
        self.intro = '\n'.join(INTRO)
 	initdb()
        self.cmdloop()

    def do_help(self, line):
        print "this is da help"
    
    def default(self, line):
        print '\n'.join(['Command not found.', INTRO[1]])

    def initdb(self):
        c.execute('''CREATE TABLE IF NOT EXIST taskrecords  (id INTEGER PRIMARY KEY, user_id INTEGER, description TEXT, task TEXT, start_date DATE, end_date DATE, estimated_time INTEGER, worked_timed INTEGER, tags TEXT)''') 
        c.execute('''CREATE TABLE IF NOT EXIST users  (id INTEGER PRIMARY KEY, realname TEXT, password_hash TEXT, password_salt TEXT, last_login DATE) ''')
        c.commit() 
        
if __name__ == '__main__':
    p = Ptask()
