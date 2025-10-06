from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket
)

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieDetailSerializer,
    MovieListSerializer,
    MovieSessionSerializer,
    MovieSessionListWithTicketsSerializer,
    MovieSessionDetailWithPlacesSerializer,
    OrderSerializer,
    OrderCreateSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = PageNumberPagination


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    pagination_class = PageNumberPagination


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    pagination_class = PageNumberPagination


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.all()

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        genres_param = self.request.query_params.get("genres")
        if genres_param:
            try:
                genres = [int(g) for g in genres_param.split(",") if g]
                queryset = queryset.filter(genres__id__in=genres).distinct()
            except ValueError:
                pass

        actors_param = self.request.query_params.get("actors")
        if actors_param:
            try:
                actors = [int(a) for a in actors_param.split(",") if a]
                queryset = queryset.filter(actors__id__in=actors).distinct()
            except ValueError:
                pass

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related("movie", "cinema_hall").prefetch_related("tickets")
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset
        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(show_time__date=date)
        movie_id = self.request.query_params.get("movie")
        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListWithTicketsSerializer
        if self.action == "retrieve":
            return MovieSessionDetailWithPlacesSerializer
        return MovieSessionSerializer

    @action(detail=True, methods=["get"])
    def taken_places(self, request, pk=None):
        movie_session = self.get_object()
        tickets = movie_session.tickets.all()
        taken_places = [{"row": ticket.row, "seat": ticket.seat} for ticket in tickets]
        return Response(taken_places)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall"
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
