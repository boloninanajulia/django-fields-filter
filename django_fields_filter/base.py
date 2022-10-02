from abc import ABC, abstractmethod


class BaseFilterBackend(ABC):
    """
    A base class from which all filter backend classes should inherit.
    """

    @abstractmethod
    def filter_queryset(self, request, queryset, view=None):
        """
        Return a filtered queryset.
        """
        raise NotImplementedError(".filter_queryset() must be overridden.")
