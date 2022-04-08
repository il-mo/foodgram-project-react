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

    @action(
        detail=True,
        permission_classes=[IsAuthenticated],
        methods=['POST', 'DELETE'],
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            author = get_object_or_404(User, id=id)
            if self.request.user.id == author:
                return Response(
                    {'errors': 'Вы не можете подписываться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Follow.objects.filter(
                author_id=author.id, user_id=self.request.user.id
            ).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на данного пользователя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Follow.objects.create(
                author_id=author.id, user_id=self.request.user.id
            )
            serializer = FollowSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if self.request.user.id == author:
                return Response(
                    {'errors': 'Вы не можете отписываться от самого себя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            follow = Follow.objects.filter(
                author_id=author.id, user_id=self.request.user.id
            )
            if follow.exists():
                follow.delete()
                return Response(
                    {'status': 'Вы успешно отписались от пользователя'},
                    status=status.HTTP_200_OK,
                )

            return Response(
                {'errors': 'Вы не подписаны на данного пользователя'},
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
