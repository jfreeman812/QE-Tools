#! /bin/bash

# Used to verify pytest tests
# Modified from existing verify-tests.sh from Unittest/OpenCafe tests

export PYTHONPATH=.:../../qe_coverage


# First, test test_decorators.py. Should be all positive
echo "A good run, no ERRORs or FAILures should happen below:"
args_list="--qe-coverage --environment staging --no-report "
args_list="${args_list} -vvv --capture no"

RESULTS="$(pytest ${args_list} test_decorators.py)"
echo "==========================================="
echo "Anything in below section indicates test"
echo "failure or error in test"
echo "-------------------------------------------"
echo -e "${RESULTS}" | grep -e "FAILED" -e "ERROR"
echo -e "${RESULTS}" | grep "test_ok" | grep "SKIPPED"
echo -e "${RESULTS}" | grep "test_skipped" | grep "PASSED"
echo "==========================================="



# wrap run of bad_decorators.py, should fail with ValueError
# exception because of test setup hook
args_list="--qe-coverage --environment staging --no-report "
args_list="${args_list} --capture no"
BAD_RESULTS="$(pytest ${args_list} bad_decorators.py)"
echo  "${BAD_RESULTS}" | grep -q "ValueError:"
BAD_RETURN=$?
echo ""
echo ""
echo ""
echo "Testing bad run"
echo "==========================================="
if [[ BAD_RETURN -eq 0 ]]; then
    echo "Pytest negative test successful (received expected ValueError)"
else
    echo "Pytest negative test failed (did not receive expected ValueError)"
    echo "-------------------------------------------"
    echo -e "${RESULTS}"
fi
echo "==========================================="
