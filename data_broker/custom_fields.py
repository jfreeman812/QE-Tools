from flask_restplus import fields
import qe_coverage.base


def labels_from(table_name):
    table = qe_coverage.base.coverage_tables[table_name]
    return [x for x in table.get_fields('report_as') if not x.startswith('``')]


def validate_fields(payload, api_model, field_name_alternates=None):
    messages = []
    field_name_alternates = field_name_alternates or {}
    for main, alternate in field_name_alternates.items():
        both_missing_or_both_provided = (main in payload) is (alternate in payload)
        if both_missing_or_both_provided:
            messages.append('Either {} or {} are required, but not both.'.format(main, alternate))
            continue
        if alternate in payload:
            payload[main] = payload.pop(alternate)
    for key in api_model:
        if api_model[key].required and key not in payload:
            messages.append('Missing required key "{}"'.format(key))
    for key in payload:
        if key not in api_model:
            continue
        field = api_model[key]
        if isinstance(field, fields.List):
            field = field.container
            data = payload[key]
        else:
            data = [payload[key]]
        if isinstance(field, CustomField) and hasattr(field, 'validate'):
            for i in data:
                messages.append(field.validate(i))
    return list(filter(None, messages))


def validate_response_list(response_list, api_model, label_name, field_name_alternates=None):
    collected_errors = []
    for entry in response_list:
        errors = validate_fields(entry, api_model, field_name_alternates)
        if errors:
            collected_errors.append({label_name: entry[label_name], 'errors': errors})
    rejected_labels = {x[label_name] for x in collected_errors}
    valid_responses = [x for x in response_list if x[label_name] not in rejected_labels]
    return valid_responses, collected_errors


class CustomField(fields.String):
    pass


class CoverageField(CustomField):
    '''
    Base class for validation of coverage data
    against the allowed values for a given field.
    '''
    table_name = None

    def validate(self, value):
        labels = labels_from(self.table_name)
        if value not in labels:
            message = '"{}" is not a valid option for {}: {}'
            return message.format(value, self.table_name, labels)
        return ''


class InterfaceType(CoverageField):
    table_name = 'Interface Type'


class Polarity(CoverageField):
    table_name = 'Polarity'


class Priority(CoverageField):
    table_name = 'Priority'


class Suite(CoverageField):
    table_name = 'Suite'


class Status(CoverageField):
    table_name = 'Status'


class ExecutionMethod(CoverageField):
    table_name = 'Execution Method'


class ProductHierarchy(CustomField):
    hierarchy_separator = '::'
    expected_hierarchy_levels = 2

    def validate(self, value):
        found_levels = len(value.split(self.hierarchy_separator))
        if found_levels != self.expected_hierarchy_levels:
            message = ('"{}" does not contain the expected Product Hierarchy format of '
                       '{} levels with a "{}" separator')
            return message.format(value, self.expected_hierarchy_levels, self.hierarchy_separator)
        return ''


class TicketId(CustomField):
    def validate(self, value):
        ticket_re = qe_coverage.base.TICKET_RE
        if not ticket_re.match(value):
            return '"{}" does not match Ticket pattern: {}'.format(value, ticket_re.pattern)
        return ''
