#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from app import create_app, db
from app.models import User, Question, Answer, Follow, Activity
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default') 
manager = Manager(app)
migrate = Migrate(app, db)

#put app/db/User in shell, and dont need to import
def make_shell_context():
    return dict(app=app, db=db, User=User, Follow=Follow, Question=Question, Answer=Answer, Activity=Activity) 
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

@manager.command
# function name means command name
def test():
    """Run the unit tests."""
    import unittest
    # 'tests' means file folder name
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == '__main__':
    manager.run()