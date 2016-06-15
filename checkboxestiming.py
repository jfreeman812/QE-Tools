import json
import sys
from collections import namedtuple
from datetime import datetime as DT
decode_fmt = "%Y-%m-%dT%H:%M:%S.%fZ"

# This script will analyze the action times for the CheckBoxes process.
# It was a quick and dirty hack and does not handle the case where
# the process has been resumed, such as if the initial call to architect
# times out and the process halts. The goal here was to figure out from
# a successful, but slow, run of CheckBoxes if there are any patterns
# by seeing which actions where slow.

myName = sys.argv[0]
inputName = None
TimingData = namedtuple("TimingData", ["time", "action", "host"])

try:
    inputName, = sys.argv[1:]
except:
    print "Usage:", myName, "file-to-analyze"
    sys.exit(-1)


def trim_log_time(ts):
    # All this string hacking is because the timestamps
    # in the JSON can have "interesting formating" that will
    # cause errors with strptime, so this makes sure that
    # we'll get a good conversion. We're not worried about losing
    # or obscuring the nanoseconds part of the time.
    ts = ts[:-2]
    if len(ts) < 22:
        ts += "00"
    return ts+"Z"

print "analyzing", inputName
event = json.load(open(inputName))
steps = event['Automation']['ExecutionSteps'][2]['ExecutionSteps']
print
print "Slow steps:"
slow_steps = []
for step in steps:
    logs = step.get("Logs")
    if 'ExecutionSteps' in step:
        del step['ExecutionSteps']
    if logs is None:
        continue
    log_times = map(logs.get, ['ACCEPTED', 'PROCESSING', 'COMPLETED'])
    if not all(log_times):  # unless all timestamps are present, ignore
        continue
    log_times = map(trim_log_time, log_times)
    stamps = map(lambda x: DT.strptime(x, decode_fmt), log_times)
    first = min(stamps)
    last = max(stamps)
    delta = last - first
    if delta.total_seconds() > 1.2:
        slow_steps.append((delta, step))

slow_details = []

for delta, step in slow_steps:
    print "This step took", delta, "seconds"
    json.dump(step, sys.stdout, indent=2, sort_keys=True,
              separators=(',', ':'))
    details = step.get("Details")
    id_ = details.get("ID")
    params_ = details.get("InputParams")
    if params_:
        host_ = params_[0].get("ParameterValue")
        slow_details.append(TimingData(time=delta, action=id_, host=host_))
    print
    print


def print_timing_line(timing_data):
    print "%-15s %s %s" % (timing_data.host,
                           timing_data.time,
                           timing_data.action)

print "Slowness by Action:"
for timing_data in sorted(slow_details, key=lambda x: (x.action, x.host)):
    print_timing_line(timing_data)

print
print
print "Slowness by Host:"
for timing_data in sorted(slow_details, key=lambda x: (x.host, x.action)):
    print_timing_line(timing_data)
