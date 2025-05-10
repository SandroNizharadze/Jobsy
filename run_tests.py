#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    # Make sure Django knows we're testing
    os.environ['DJANGO_SETTINGS_MODULE'] = 'jobsy.settings'
    os.environ['DJANGO_TEST_MODE'] = 'True'
    
    # Set up Django
    django.setup()
    
    # Get and run test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    # Run the tests
    tests_to_run = sys.argv[1:] or ['core.tests']
    failures = test_runner.run_tests(tests_to_run)
    
    # Exit with proper code
    sys.exit(bool(failures)) 