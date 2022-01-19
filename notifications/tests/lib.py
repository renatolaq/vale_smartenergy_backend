language_strings_module = [
    {"module": "USAGE_CONTRACT", "string": '${connection_point}=="N"', "lexeme_length": 3},
    {
        "module": "USAGE_CONTRACT",
        "string": "${create_date}<{data:2020/12/22}",
        "lexeme_length": 3,
    },
    {
        "module": "USAGE_CONTRACT",
        "string": "${create_date}<={currentDate}-5",
        "lexeme_length": 5,
    },
    {
        "module": "USAGE_CONTRACT",
        "string": "${create_date}==${end_date}",
        "lexeme_length": 3,
    },
    {
        "module": "USAGE_CONTRACT",
        "string": '${connection_point}=="N"&&${create_date}<={currentDate}',
        "lexeme_length": 7,
    },
    {
        "module": "USAGE_CONTRACT",
        "string": '(${contract_value}>15000||${connection_point}=="N")&&${create_date}<={currentDate}',
        "lexeme_length": 13,
    },
    {
        "module": "USAGE_CONTRACT",
        "string": '${connection_point}=="N"&&${create_date}<={currentDate}||${contract_value}>15000',
        "lexeme_length": 11,
    },
    {
        "module": "USAGE_CONTRACT",
        "string": "${create_date}>{currentDate}&&(${create_date}>{currentDate}||${create_date}>{currentDate})",
        "lexeme_length": 13,
    },
    {
        "module": "USAGE_CONTRACT",
        "string": '((${connection_point}!="S"))&&(${contract_value}>(${contract_number}*(${contract_number}*1)))&&(${end_date}==${start_date}+31)||(${create_date}>=({currentDate}+2))',
        "lexeme_length": 39,
    },
    {
        "module": "USAGE_CONTRACT",
        "string": '${contract_value}!=14587.55',
        "lexeme_length": 3,
    },
    {
        "module": "USAGE_CONTRACT",
        "string": '${contract_value}!=14587.55+422',
        "lexeme_length": 5,
    },
]

incorrect_language_strings_module = [
    {"module": "USAGE_CONTRACT", "string": '${connection_point}=="N"+5', "lexeme_length": 5},
    {
        "module": "USAGE_CONTRACT",
        "string": "15==${contract_value}",
        "lexeme_length": 3,
    },
    {
        "module": "USAGE_CONTRACT",
        "string": '${contract_value}!=14587.55+"dorime"',
        "lexeme_length": 3,
    },
]

logical_operation_dict = {
    "type": "logical_operation",
    "operator_left": {
        "type": "logical_comparison",
        "field": {"value": "end_date", "type": "Database Attribute"},
        "operation": "__exact",
        "value": {"value": "end_date", "type": "Database Attribute"},
    },
    "operation": "||",
    "operator_right": {
        "type": "logical_comparison",
        "field": {"value": "create_date", "type": "Database Attribute"},
        "operation": "__gte",
        "value": {"value": "create_date", "type": "Database Attribute"},
    },
}

logical_comparison_dict = {
    "type": "logical_comparison",
    "field": {"value": "connection_point", "type": "Database Attribute"},
    "operation": "__exact",
    "value": {"value": "N", "type": "String"},
}

aritimetical_operation_dict = {
    "type": "aritimetical_operation",
    "operator_left": {"value": "currentDate", "type": "Variable"},
    "operation": "+",
    "operator_right": {"value": "2", "type": "Number"},
}

value_dict = {"value": "N", "type": "String"}


class MockQuerySet:
    def __init__(self, values):
        self.values = values
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):  # Python 2: def next(self)
        self._index += 1
        if self._index >= len(self.values):
            raise StopIteration
        return self.values[self._index]

    def exclude(self, *args, **kwargs):
        return []


class MockMail:
    def __init__(self):
        self.target_email = "example@example.example"

    def all(self):
        return [self]

class MockMailField:
    def __init__(self):
        self.email_field = "contract_value"

    def all(self):
        return [self]

class MockNotificationMail:
    def __init__(self, **kwargs):
        self.pk = kwargs["pk"]
        self.entity = kwargs["entity"]
        self.notification_rule_processed = kwargs["notification_rule_processed"]
        self.message = kwargs["message"]
        self.subject = kwargs["subject"]
        self.emails = MockMail()
        self.email_fields = MockMailField()