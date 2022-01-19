class PaginatedDataFactory:
    @classmethod
    def get_paginated_data(cls, paginator=None):
        if paginator is None:
            return {'count': 0, 'next': None, 'previous': None, 'report_name': None, 'referenced_report_name': None, 'month': None, 'year': None, 'limit_ccee_vale': None, 'results': []}
        result = {'count': paginator.page.paginator.count, 'next': paginator.get_next_link(), 'previous': paginator.get_previous_link(), 'report_name': paginator.page.object_list[0].report_name, 'month': paginator.page.object_list[0].referencing_month, 'year': paginator.page.object_list[0].referencing_year, 'limit_ccee_vale': paginator.page.object_list[0].limit_value, 'results': paginator.page.object_list}
        return result
