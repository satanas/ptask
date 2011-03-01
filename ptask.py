#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import cmd
import time
import random
import getpass
import hashlib
import sqlite3

HLINE = '=' * 80
DATABASE = 'ptask.db'
NULL_FIELD = ' (leave blank for null)'
WRONG_CMD = "Wrong command. Type help"

INPUT_NUM = 'num'
INPUT_DATE= 'date'
INPUT_TEXT = 'text'
INPUT_PASS = 'passwd'

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
    start_date FLOAT, 
    end_date FLOAT, 
    estimated_time FLOAT, 
    worked_time FLOAT, 
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
    (user_id, description, task, start_date, end_date, estimated_time, 
    worked_time, tags) VALUES (?,?,?,?,?,?,?,?)'''

SQL_UPDATE_LAST_LOGIN = '''UPDATE users SET last_login=? WHERE id=?'''

SQL_SELECT_TASK = '''SELECT * FROM taskrecords WHERE id=?'''

SQL_START_TASK = '''UPDATE taskrecords SET start_date=?,end_date=NULL WHERE id=?'''

SQL_STOP_TASK = '''UPDATE taskrecords SET end_date=?,worked_time=? WHERE id=?'''

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
    
    # utils
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
        
    def __get_current_time(self):
        return time.strftime('%d/%m/%Y %H:%M', time.localtime(time.time()))
    
    def __get_arg_value(self, arg, index):
        try:
            return arg[index]
        except IndexError:
            return None
            
    def __cut_field(self, field, size):
        if len(field) > size:
            field = field[0:size-3] + '...'
        return field
        
    def __last_login(self):
        d = self.__get_current_time()
        cursor = self.conn.cursor()
        cursor.execute(SQL_UPDATE_LAST_LOGIN, (d, self.user_id))
        self.conn.commit()

    def __validate_date(self, date):
        try:
            date = time.strptime(date, '%d/%m/%Y')
            return date
        except ValueError, TypeError:
            return None

    def __validate_number(self, number):
        try:
           return float(number)
        except ValueError:
           return None
        
    def __user_input(self, caption, type=INPUT_TEXT, null=False, options=None):
        #TODO: Implement size validation
        
        rtn = None
        #First item in options get default
        if options:
            opt_str =' ['
            for i in range(len(options)):
                opt_str += options[i].upper() if i == 0 else options[i].lower()
                opt_str += '\\' if (i != len(options) - 1) else ''
            opt_str += ']'
        else:
            opt_str = ''
            
        if null:
            caption += NULL_FIELD
        
        while not rtn:
            if type == INPUT_PASS:
                rtn = getpass.getpass('%s: ' % caption)
            else:
                rtn = raw_input('%s%s: ' % (caption, opt_str))
            
            if (not null and rtn == '' and not options):
                print "%s can't be empty. Please insert a valid value" % caption
                continue
            elif (null and rtn == '' and not options):
                return None
                
            if (type == INPUT_DATE):
                rtn = self.__validate_date(rtn)
                if not rtn:
                    print "Please insert a valid date"
                    continue
            elif (type == INPUT_NUM):
                rtn = self.__validate_number(rtn)
                if not rtn:
                    print "Please insert a valid number"
                    continue
            if options:
                if rtn == '':
                    rtn = options[0]
                else:
                    rtn = rtn.lower()
                    if rtn not in options:
                        print "Please insert a valid value%s" % opt_str
                        rtn = None
                        continue
            return rtn
        
    def __initdb(self):
        if not os.path.isfile(DATABASE):
            self.conn = sqlite3.connect(DATABASE)
            cursor = self.conn.cursor()
            cursor.execute(SQL_TASK_TABLE) 
            cursor.execute(SQL_USER_TABLE)
            self.conn.commit()
            print "Database has been created. Now you need to create a user..."
            self.__create_user(is_admin=True, validate=True)
        else:
            self.conn = sqlite3.connect(DATABASE)
            self.__login()
    
    #users functions        
    def __login(self):
        #TODO: Validate when user is not in DB
        while 1:
            user = ''
            pwd = ''
            while user == '':
                user = raw_input('Username: ')
            while pwd == '':
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
            if self.last_login:
                print "Last login: %s " % str(self.last_login)
            return True
        
    def __create_user(self, is_admin=False, validate=False):
        realname = self.__user_input('Real name')
        username = self.__user_input('Username')

        if is_admin:
            admin = 1
        else:
            admin = self.__user_input('Admin?', options=['y', 'n'])
            admin = 1 if (admin == 'y') else 0
        
        while 1:
            pwd = self.__user_input('Password', type=INPUT_PASS)
            repwd = self.__user_input('Password again', type=INPUT_PASS)
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
        if validate:
            self.__validate_credentials(username, pwd)
        
    def __list_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users")
        print '\n\t\t\tUsers list'
        print HLINE
        print "%-20s %-20s %s\t %s" % ('Username', 'Real Name', 'Admin?', 
            'Last Login')
        print HLINE
        for row in cursor:
            admin = 'True' if row[6] == 1 else 'False'
            print "%-20s %-20s %s\t\t %s" % (row[1], row[2], admin, row[5])
        print '\n'

    #task functions
    
    def __create_task(self):
        worked = None
        start_date = None
        oldtask = self.__user_input('Task already started?', options=['y', 'n'])
        name = self.__user_input('Task name')
        description = self.__user_input('Description')
        estimated = self.__user_input('Estimated time', type=INPUT_NUM, null=True)
        if oldtask == 'y':
            worked = self.__user_input('Worked time', type=INPUT_NUM, null=True)
        tags = self.__user_input('Tags', null=True)
        start = self.__user_input('Start?', options=['y', 'n'])
        start = 1 if (start == 'y') else 0
        cursor = self.conn.cursor()
        
        if start:
            start_date = self.__get_current_time()
            message = "Task created and started successfully!"
        else:
            message = "Task created successfully!"
        
        cursor.execute(SQL_CREATE_TASK, (self.user_id, description, name, 
            start_date, None, estimated, worked, tags))
        self.conn.commit()
        print message
        
    def __list_task(self, from_user=None):
        #TODO: Show marks in tasks that are actually running
        cursor = self.conn.cursor()
        if from_user:
            cursor.execute("SELECT * FROM taskrecords WHERE user_id=?", 
                (from_user,))
        else:
            cursor.execute("SELECT * FROM taskrecords")
        results = cursor.fetchall()
        print '\t\t\t\ttasks'
        print HLINE
        print "%-3s %-12s %-40s %-10s %-10s" % ('id','Name', 'Description', 
            'Estimated', 'Worked')
        print HLINE
        for row in results:
            name = self.__cut_field(row[3], 12)
            desc = self.__cut_field(row[2], 40)
            print "%-3d %-12s %-40s %-10s %-10s" % (row[0], name, desc, row[6], 
                row[7])
        print "\nTotal: %d task(s)" % len(results)
       
    def __show_task(self, args):
        #TODO: Optimize screen space
        if self.__validate_number(args[1]):
            task_id = args[1]
        else:
            print "Please insert a valid task id"
            return
        cursor = self.conn.cursor()
        cursor.execute(SQL_SELECT_TASK, (task_id,))
        row = cursor.fetchone()
        if row == None:
            print "Task not found!"
            return
        print '\n\t\t\tTask: %s' % row[3]
        print HLINE
        print "id:        %d" % row[0]
        print "name:      %s" % row[3]
        print "desc:      %s" % row[2]
        print "started    %s" % row[4]
        print "end:       %s" % row[5]
        print "estimated: %s h" % row[6]
        print "worked:    %s h" % row[7]
        print "tags:      %s" % row[8]
        print '\n'
        
    def __start_task(self, task_id):
        #TODO: Stop any other task
        cursor = self.conn.cursor()
        cursor.execute(SQL_SELECT_TASK, (task_id,))
        row = cursor.fetchone()
        if row == None:
           print "Task not found!"
           return
        start_date = self.__get_current_time()
        cursor.execute(SQL_START_TASK, (start_date, task_id))
        self.conn.commit()
        print "Task %s started successfully" % task_id
        
    def __stop_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute(SQL_SELECT_TASK, (task_id,))
        row = cursor.fetchone()
        if row == None:
           print "Task not found!"
           return
        start_date = row[4]
        worked_time = row[7]
        if worked_time is None:
            worked_time = 0
        end_date = self.__get_current_time()
        start_secs = time.mktime(time.strptime(start_date, '%d/%m/%Y %H:%M'))
        end_secs = time.mktime(time.strptime(end_date, '%d/%m/%Y %H:%M'))
        this_work = (end_secs - start_secs)/3600
        worked_time += this_work
        cursor.execute(SQL_STOP_TASK, (end_date, worked_time, task_id))
        self.conn.commit()
        print "Task %s stoped successfully" % task_id
        print "You've worked %.2fh in this task for a total of %.2fh" % 
            (this_work, worked_time)
        
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
        else:
            print WRONG_CMD

    def do_task(self, args):
        arg = args.split()
        if len(arg) < 1:
            print '\n'.join(MISSING)
            return
        if arg[0] == 'add':
            self.__create_task()
        elif arg[0] == 'list':
            user_id = self.__get_arg_value(arg, 1)
            self.__list_task(user_id)
        elif arg[0] == 'show':
            if len(arg) < 2:    
               print '\n'.join(MISSING)
            else:
               self.__show_task(arg)
        elif arg[0] == 'start':
            if len(arg) < 2:    
               print '\n'.join(MISSING)
            else:
               self.__start_task(arg[1])
        elif arg[0] == 'stop':
            if len(arg) < 2:    
               print '\n'.join(MISSING)
            else:
               self.__stop_task(arg[1])
        else:
            print WRONG_CMD

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
            '    list <user_id> - Show list of all tasks for user with id <user_id>',
            '    show <id> - Show details of the task with <id>',
            '    start <id> - Start the time tracking for the task with <id>',
            '    stop <id> - Stop the time tracking for the task with <id>',
        ])
       
    def help_help(self):
        print 'Show this help'
        
    def help_exit(self):
        print 'Duh! Exit'
    
    def help_EOF(self):
        print 'Duh! Exit'
        
if __name__ == '__main__':
    p = Ptask()
