#!/bin/bash

# Activate the virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Set test module based on argument or default to all tests
TEST_MODULE=${1:-core.tests}

# Run the tests
python run_tests.py $TEST_MODULE

# Exit with the status from the tests
exit $? 