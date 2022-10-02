from datetime import datetime

from django.db import models
from django.core.exceptions import FieldError

from .base import BaseFilterBackend


class FieldsFilterBackend(BaseFilterBackend):
    """
    Filtering by fields with Django's ORM filters (<lookup_keyword>)
    Example: ?field_name__lookup_keyword=value
    Example: ?field_name(foreign_key)__field_name_of_related_model__....__lookup_keyword=value
    """

    separator = '__'

    def get_field_of_model(self, model, field_name):
        try:
            field = model._meta.get_field(field_name)
        except LookupError:
            field = None

        return field

    def get_field_name_and_postfix_from_filter_param(self, filter_param):
        separator_index = filter_param.find(self.separator)
        if separator_index == -1:
            return filter_param, None

        field_name = filter_param[0:separator_index]
        postfix = filter_param[separator_index + len(self.separator):]

        return field_name, postfix

    def get_field_and_postfix(self, model, filter_param):
        field_name, postfix = self.get_field_name_and_postfix_from_filter_param(filter_param)

        field = self.get_field_of_model(model, field_name)
        return field, postfix

    def filter_queryset(self, request, queryset, view=None):
        request_query_items = self.get_request_query_items(request)

        for filter_param, value in request_query_items:

            model = queryset.model
            field, postfix = self.get_field_and_postfix(model, filter_param)

            if field:
                queryset = self.rebuild_queryset(
                    queryset, field, value, postfix
                )

        return queryset

    @staticmethod
    def get_request_query_items(request) -> list:
        return list(map(lambda k: (k[0], k[1]), request.GET.items()))

    def rebuild_queryset(self, queryset, field, value, postfix=None):
        field_name = field.name
        value, postfix = self.prepare_filter_attributes(field, value, postfix)

        try:
            filters = self.get_filters_as_dict(field_name, value, postfix)
            return queryset.filter(**filters)
        except (ValueError, FieldError):
            raise Exception('The parameter is invalid')

    def prepare_filter_attributes(self, field, value, postfix=None, depth=0):
        postfix_ = None

        if isinstance(field, models.ForeignKey):
            model = field.remote_field.model
            if postfix:
                field, postfix_ = self.get_field_and_postfix(model, filter_param=postfix)
                value, postfix_ = self.prepare_filter_attributes(field, value, postfix=postfix_, depth=depth+1)

        # for CharField (Contains the phrase, but case-insensitive)
        elif isinstance(field, models.CharField) and not postfix:
            postfix_ = 'icontains'

        # for DateTime in format %Y-%m-%d (Matches a date)
        elif isinstance(field, models.DateTimeField) \
                and (postfix is None or postfix in ('lt', 'gt')) \
                and datetime.strptime(value, '%Y-%m-%d'):
            postfix_ = 'date'

        # for several values
        elif postfix == 'in':
            value = value.split(',')

        filter_type = self.rebase_filter_postfix(postfix, postfix_) if depth == 0 else postfix_
        return value, filter_type

    @staticmethod
    def rebase_filter_postfix(postfix_base, postfix=None) -> str:
        return f'{postfix_base}__{postfix}' if postfix else postfix_base

    @staticmethod
    def get_filters_as_dict(field_name, value, postfix=None) -> dict:
        if not postfix:
            return {field_name: value}
        return {f"{field_name}__{postfix}": value}
