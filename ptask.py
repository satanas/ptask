#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import cmd
import getpass
import random
import time
from datetime import date
import hashlib
import hashlib
import sqlite3

DATABASE = 'ptask.db'

INTRO = [
    '\nWelcome to ptask', 
    'Type "help" to get a list of available commands.',
]

MISSING = [
    'ERROR: Missing arguments',
    'Type "help" for a list of available commands.',
    'Type "help <command>" for a detailed help about the command'
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

SQL_CREATE_TASK = '''INSERT INTO taskrecords 
    (user_id, description, task, start_date, end_date, estimated_time, worked_time, tags)
    VALUES (?,?,?,?,?,?,?,?)'''

SQL_UPDATE_LAST_LOGIN = '''UPDATE users SET last_login=? WHERE id=?'''

class Ptask(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = 'ptask> '
        self.intro = '\n'.join(INTRO)
        self.admin = False
        try:
            self.__initdb()
            self.cmdloop()
        except KeyboardInterrupt:
            self.do_exit('')
    
    #utils    
    def __confirm_passwords(self, pwd1, pwd2):
        if pwd1 == pwd2:
            return True
        else:
            return False
        
    def __generate_salt(self):
        s = ""
        for i in range(6):
            s += chr(random.randrange(65,128))        
        return s

    def __last_login(self):
        #FIXME: There is a better implementation for sure! ;)
        d = str(date.today().day)+'/'+str(date.today().month)+'/'+str(date.today().year)
        cursor = self.conn.cursor()
        cursor.execute(SQL_UPDATE_LAST_LOGIN, (d,self.user_id))
        self.conn.commit()


    def __valid_date(self,date):
        try:
            date = time.strptime(date, '%d/%m/%Y')
            return True
        except ValueError:
            return False
        
    def __initdb(self):
        if not os.path.isfile(DATABASE):
            self.conn = sqlite3.connect(DATABASE)
            cursor = self.conn.cursor()
            cursor.execute(SQL_TASK_TABLE) 
            cursor.execute(SQL_USER_TABLE)
            self.conn.commit()
            print "Database has been created. Now you need to create a user..."
            self.__create_user(is_admin=True)
        else:
            self.conn = sqlite3.connect(DATABASE)
            self.__login()
    
    #users functions        
    def __login(self):
        while 1:
            user = raw_input('Username: ')
            pwd = getpass.getpass('Password: ')
            if self.__validate_credentials(user, pwd):
               break
            else:
               print 'Invalid credentials!. Try again'
        
    def __validate_credentials(self, user, pwd):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (user,))
        row = cursor.fetchone()
        
        stored_hash = row[3]
        pwd_salt = row[4]
        admin = row[6]
        
        m = hashlib.md5()
        m.update(pwd + pwd_salt)
        pwd_hash = m.hexdigest()
        
        if pwd_hash != stored_hash:
            return False
        else:
            self.admin = True if admin == 1 else False
            self.user_name = row[1]
            self.user_id = row[0]
            self.last_login = row[5]
            print "last login: %s " % str(self.last_login)
            return True
        
    def __create_user(self, is_admin=False):
        realname = raw_input('Real name: ')
        username = raw_input('Username: ')
        
        if len(realname) < 3:
           print 'Real name must be more than 2 characters!'
           return    
        if len(username) < 3:
           print 'User name must be more than 2 characters!'
           return    

        if is_admin:
            admin = 1
        else:
            admin = raw_input('Admin? [y/n]: ').lower()
            admin = 1 if (admin == 'y' or admin == '') else 0
        
        while 1:
            pwd = getpass.getpass('Password: ')
            repwd = getpass.getpass('Password again: ')
            if self.__confirm_passwords(pwd, repwd):
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
        print '\n\t\t\tUsers list'
        print "==============================================================="
        print "%-20s %-20s %s\t %s" % ('Username', 'Real Name', 'Admin?', 'Last Login')
        print "==============================================================="
        for row in cursor:
            admin = 'True' if row[6] == 1 else 'False'
            print "%-20s %-20s %s\t\t %s" % (row[1], row[2], admin, row[5])
        print '\n'


    #task functions
    
    def __create_task(self):
        name = raw_input('task name: ')
        description = raw_input('description: ')
        start = raw_input('start date (d/m/a): ')
        end = raw_input('end date (d/m/a): ')
        estimated = raw_input('estimated time: ')
        worked = raw_input('worked time: ')
        tags = raw_input('tags: ')

        if len(name) < 3:
           print 'Task name must be more than 2 characters!'
           return    
        if len(description) < 3:
           description = 'none'
        if not self.__valid_date(start) and not self.__valid_date(end):
           print 'Invalid Dates!'
        if tags == '':
           tags = 'none'
        cursor = self.conn.cursor()
        cursor.execute(SQL_CREATE_TASK, (self.user_id, description, name, start, end, estimated, worked, tags))
        self.conn.commit()
        print "Task created successfully!"
        
    def __list_task(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM taskrecords WHERE id=?", (self.user_id,))
        print '\n\t\t\t%s\'s tasks' % self.user_name
        print "==============================================================="
        print "%-20s %-20s %s\t %s" % ('Name', 'Description', 'Estimated', 'Worked')
        print "==============================================================="
        for row in cursor:
            print "%-20s %-20s %s\t\t %s" % (row[3], row[2], row[6], row[7])
        print '\n'

       
        
    #================================================
    # Commands
    #================================================
    
    def do_user(self, args):
        arg = args.split()
        if len(arg) < 1:
            print '\n'.join(MISSING)
            return
        if arg[0] == 'create':
            self.__create_user()
        elif arg[0] == 'list':
            self.__list_users()

    def do_task(self, args):
        arg = args.split()
        if len(arg) < 1:
            print '\n'.join(MISSING)
            return
        if arg[0] == 'add':
            self.__create_task()
        elif arg[0] == 'list':
            self.__list_task()




    #def do_help(self, line=None):
    #    print "this is da help"
    def do_EOF(self, line):
        return self.do_exit(line)
        
    def do_exit(self, line):
        self.__last_login()
        self.conn.close()
        print "Bye"
        return True
        
    def default(self, line):
        print '\n'.join(['Command not found.', INTRO[1]])
        
    def help_user(self):
        print '\n'.join(['Handles user operations',
            'USAGE: user <arg>',
            '  <arg>:',
            '    create - Create a new user',
            '    list - Show list of all users',
        ])

    def help_task(self):
        print '\n'.join(['Handles tasks operations',
            'USAGE: task <arg>',
            '  <arg>:',
            '    add - Add a new task',
            '    list - Show list of all tasks',
        ])
       
    def help_help(self):
        print 'Show this help'
        
    def help_exit(self):
        print 'Duh! Exit'
    
    def help_EOF(self):
        print 'Duh! Exit'
        
if __name__ == '__main__':
    p = Ptask()
