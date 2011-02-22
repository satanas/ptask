#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import cmd
import getpass
import random
import sqlite3
import hashlib

DATABASE = 'ptask.db'

INTRO = [
    'Welcome to ptask', 
    'Type "help" to get a list of available commands.',
]

SQL_TASK_TABLE = '''CREATE TABLE taskrecords (
    id INTEGER PRIMARY KEY, 
    user_id INTEGER, 
    description TEXT, 
    task TEXT, 
    start_date DATE, 
    end_date DATE, 
    estimated_time INTEGER, 
    worked_time INTEGER, 
    tags TEXT
)'''

SQL_USER_TABLE = '''CREATE TABLE users (
    id INTEGER PRIMARY KEY, 
    username TEXT,
    realname TEXT, 
    password_hash TEXT, 
    password_salt TEXT, 
    last_login DATE,
    admin BOOLEAN
) '''

SQL_CREATE_USER = '''INSERT INTO users 
    (username, realname, password_hash, password_salt, admin)
    VALUES (?,?,?,?,?)'''

class Ptask(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = 'ptask> '
        self.intro = '\n'.join(INTRO)
        self.__initdb()
        self.cmdloop()
    
    def __validate_passwords(self, pwd1, pwd2):
        if pwd1 == pwd2:
            return True
        else:
            return False
        
    def __generate_salt(self):
        s = ""
        for i in range(6):
            s += chr(random.randrange(65,128))        
        return s
    
    def __initdb(self):
        if not os.path.isfile(DATABASE):
            self.conn = sqlite3.connect(DATABASE)
            cursor = self.conn.cursor()
            cursor.execute(SQL_TASK_TABLE) 
            cursor.execute(SQL_USER_TABLE)
            self.conn.commit()
            print "Database has been created. Now you need to create a user..."
            self.__create_user(is_admin=True)
            print ""
        else:
            self.conn = sqlite3.connect(DATABASE)
        
    def __create_user(self, is_admin=False):
        realname = raw_input('Real name: ')
        username = raw_input('Username: ')
        
        if is_admin:
            admin = 1
        else:
            admin = raw_input('Admin? [y/n]: ').lower()
            admin = 1 if (admin == 'y' or admin == '') else 0
        
        while 1:
            pwd = getpass.getpass('Password: ')
            repwd = getpass.getpass('Password again: ')
            if self.__validate_passwords(pwd, repwd):
                break
            else:
                print 'Password mismatch!. Try again'
        
        pwd_salt = self.__generate_salt()
        m = hashlib.md5()
        m.update(pwd + pwd_salt)
        pwd_hash = m.hexdigest()
        cursor = self.conn.cursor()
        cursor.execute(SQL_CREATE_USER, (username, realname, pwd_hash, pwd_salt, admin))
        self.conn.commit()
        print "User created successfully!"
        
    def __list_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users")
        print "%-20s %-20s %s\t %s" % ('Username', 'Real Name', 'Admin?', 'Last Login')
        print "==============================================================="
        for row in cursor:
            admin = 'True' if row[6] == 1 else 'False'
            print "%-20s %-20s %s\t\t %s" % (row[1], row[2], admin, row[5])
    
    #================================================
    # Commands
    #================================================
    
    def do_user(self, args):
        if len(args.split()) < 1:
            self.do_help()
            return
        
        cmd = args.split()[0]
        if cmd == 'create':
            self.__create_user()
        elif cmd == 'list':
            self.__list_users()

    def do_help(self, line=None):
        print "this is da help"
    
    def default(self, line):
        print '\n'.join(['Command not found.', INTRO[1]])
        
if __name__ == '__main__':
    p = Ptask()
