from .base import BaseFilterBackend


class OrderFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view=None):
        """
        This applies to order the result queryset
        Example: ?order_by=field_name

        For reverse ordering
        Example: ?order_by=-field_name

        For several fields
        Example: ?order_by=field_name1,field_name2
        """
        if 'order_by' in request.GET:
            order_fields = request.GET['order']

            order_fields_values = order_fields.split(',')
            queryset = queryset.order_by(*[v for v in order_fields_values])

        return queryset
