from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.core.exceptions import ValidationError


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_query_param = "page"
    page_size_query_param = "limit"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )

    def validate_limit(self, value):
        try:
            limit = int(value)
        except (TypeError, ValueError):
            raise ValidationError("Limit must be an integer.")
        if limit <= 0 or limit > self.max_page_size:
            raise ValidationError(
                f"Limit must be between 1 and {self.max_page_size}."
            )
        return limit

    def paginate_queryset(self, queryset, request, view=None):
        try:
            page_number = int(request.query_params.get(self.page_query_param, 1))
        except ValueError:
            raise ValidationError("Page number must be an integer.")
        if page_number <= 0:
            raise ValidationError("Page number must be greater than zero.")

        limit = request.query_params.get(
            self.page_size_query_param, self.page_size
        )
        limit = self.validate_limit(limit)

        paginator = self.django_paginator_class(queryset, limit)
        try:
            page = paginator.page(page_number)
        except Exception as exc:
            raise ValidationError(str(exc))
        self.page = page
        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True
        return list(page)

    def get_page_size(self, request):
        limit = request.query_params.get(
            self.page_size_query_param, self.page_size
        )
        try:
            limit_int = int(limit)
        except (TypeError, ValueError):
            return None
        if limit_int <= 0 or limit_int > self.max_page_size:
            return None
        return limit_int

    def get_next_link(self):
        if not self.page.has_next():
            return None
        url = self.request.build_absolute_uri()
        page_number = self.page.next_page_number()
        return f"{url.split('?')[0]}?{self.page_query_param}={page_number}"

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        url = self.request.build_absolute_uri()
        page_number = self.page.previous_page_number()
        return f"{url.split('?')[0]}?{self.page_query_param}={page_number}"