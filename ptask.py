#!/usr/bin/python
# -*- coding: utf-8 -*-

import cmd
import sqlite3

INTRO = [
    'Welcome to ptask', 
    'Type "help" to get a list of available commands.',
]

conn = sqlite3.connect('test.db')
c = conn.cursor()

class Ptask(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = 'ptask> '
        self.intro = '\n'.join(INTRO)
        self.cmdloop()
    
    def default(self, line):
        print '\n'.join(['Command not found.', INTRO[1]])
        
if __name__ == '__main__':
    p = Ptask()
