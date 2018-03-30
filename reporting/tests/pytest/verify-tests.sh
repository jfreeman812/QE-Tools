#! /bin/bash

# Used to verify pytest tests
# Modified from existing verify-tests.sh from Unittest/OpenCafe tests

export PYTHONPATH=.:../../qe_coverage


# First, test test_decorators.py. Should be all positive
echo "A good run, no ERRORs or FAILures should happen below:"
args_list="--qe-coverage --no-report "
args_list="${args_list} -vvv --capture no"

RESULTS="$(pytest ${args_list} test_decorators.py 2>&1)"
FAILURES="$(echo "${RESULTS}" | grep -e "FAIL" -e "ERROR")"
echo "==========================================="
echo "Anything in below section indicates test"
echo "failure or error in test"
echo "-------------------------------------------"
#if [[ FAILURES ]]; then
    echo "${FAILURES}"
#fi
echo "==========================================="



# wrap run of bad_decorators.py, should fail
# exception because of test setup hook
args_list="--qe-coverage --dry-run --product-hierarchy Team::Project "
args_list="${args_list} --capture no"

# Test for two ValueErrors, one being from multiple status tags
# other being status tag not followed by ticket id
BAD_RESULTS="$(pytest ${args_list} bad_decorators.py 2>&1)"
VALUE_ERROR_RETURN=$(echo "${BAD_RESULTS}" | grep -c ": ValueError")
NOT_IMPLEMENTED_RETURN=$(echo "${BAD_RESULTS}" | grep -c ": NotImplementedError")

echo ""
echo ""
echo ""

# Test for failure in TestGroup by adding more than one suite tag
echo  "${BAD_RESULTS}" | grep -qP "test_with_conflicting_suite.*prescriptive attribute Suite.*$"
BAD_TAG_RETURN=$?
echo "Testing bad run"
echo "==========================================="
if [[ VALUE_ERROR_RETURN -eq 2  && BAD_TAG_RETURN -eq 0 && NOT_IMPLEMENTED_RETURN -eq 1 ]]; then
    echo "Pytest negative test successful"
else
    echo "Pytest negative test failed"
    echo "-------------------------------------------"
    echo -e "${BAD_RESULTS}"
fi
echo "==========================================="
