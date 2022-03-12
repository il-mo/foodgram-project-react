from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.paginations import PagePagination
from api.serializers import FollowSerializer
from users.models import Follow, User
from users.serializers import CustomUserSerializer


class CustomUserViewSet(UserViewSet):
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()
    pagination_class = PagePagination

    # @action(
    #     methods=['GET'],
    #     detail=False,
    #     permission_classes=[IsAuthenticated],
    #     url_path='me',
    # )
    # def show_profile(self, request):
    #     serializer = self.get_serializer(request.user)
    #     return Response(serializer.data)
    #
    # @action(
    #     methods=['GET'],
    #     detail=False,
    #     permission_classes=[IsAuthenticated],
    #     url_path='subscriptions',
    # )
    # def show_subscriptions(self, request):
    #     author_ids = Follow.objects.filter(
    #         user_id=self.request.user.id
    #     ).values_list('author', flat=True)
    #     data = self.filter_queryset(
    #         User.objects.filter(id__in=author_ids).all()
    #     )
    #     page = self.paginate_queryset(data)
    #     serializer = FollowSerializer(page, context=request, many=True)
    #     if page is not None:
    #         return self.get_paginated_response(serializer.data)
    #     return Response(serializer.data, {'filter': filter})
    #
    # @action(
    #     methods=['POST', 'DELETE'],
    #     detail=False,
    #     permission_classes=[IsAuthenticated],
    #     url_path='(?P<id>[0-9]+)/subscribe',
    # )
    # def subscribe(self, request, id):
    #     author = get_object_or_404(User, id=id)
    #
    #     if request.method == 'POST':
    #
    #         if Follow.objects.filter(
    #                 author_id=author.id, user_id=self.request.user.id
    #         ).exists():
    #             raise ValidationError(
    #                 detail={
    #                     'error': ['Вы уже подписаны на данного пользователя']
    #                 }
    #             )
    #         Follow.objects.create(
    #             author_id=author.id, user_id=self.request.user.id
    #         )
    #         serializer = FollowSerializer(author, context=request)
    #         return Response(serializer.data)
    #
    #     if request.method == 'DELETE':
    #         try:
    #             Follow.objects.get(
    #                 author_id=author.id, user_id=self.request.user.id
    #             ).delete()
    #             return Response(
    #                 {'status': 'Вы успешно отписались от пользователя'},
    #                 status=status.HTTP_200_OK,
    #             )
    #         except Exception:
    #             raise ValidationError(
    #                 detail={
    #                     'error': [
    #                         'Вы не были подписаны на данного пользователя'
    #                     ]
    #                 }
    #             )
    @action(
        detail=True,
        permission_classes=[IsAuthenticated],
        methods=['POST', 'DELETE'],
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Вы не можете подписываться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на данного пользователя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            follow = Follow.objects.create(user=user, author=author)
            serializer = FollowSerializer(follow, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if user == author:
                return Response(
                    {'errors': 'Вы не можете отписываться от самого себя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            follow = Follow.objects.filter(user=user, author=author)
            if follow.exists():
                follow.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response(
                {'errors': 'Вы уже отписались'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        author_ids = Follow.objects.filter(
            user_id=self.request.user.id
        ).values_list('author', flat=True)
        data = self.filter_queryset(
            User.objects.filter(id__in=author_ids).all()
        )
        page = self.paginate_queryset(data)
        serializer = FollowSerializer(
            page, context={'request': request}, many=True
        )
        return self.get_paginated_response(serializer.data)
