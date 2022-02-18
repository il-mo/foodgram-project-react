from rest_framework.pagination import PageNumberPagination


class PagePagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'limit'
    max_page_size = 10
