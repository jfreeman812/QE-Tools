'''
The version name for the DataBroker schema currently being sent to Splunk.

Warning:
    Changing the value in this module also requires a corresponding change
    to the Splunk dashboard that handles the data sent from the Data Broker.
    Do not change this value unless you simultaneously coordinate the
    additional changes needed in the Splunk dashboard.
'''

SCHEMA_VERSION = 'qe_coverage_metrics_schema_v20180525'
