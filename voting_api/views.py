from django.db import IntegrityError, transaction
from django.db.models import Q, Count
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Seat, Candidate, Vote
from .serializers import (
    VoterRegistrationSerializer,
    VoterLoginSerializer,
    SeatSerializer,
    CandidateSerializer,
    VoteSerializer,
)


# ── Public endpoints ──────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def index(request):
    return Response("Hello Timo")


@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    serializer = VoterRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        voter = serializer.save()
        return Response(
            {"message": "Registration successful", "voter_code": voter.voter_code},
            status=status.HTTP_201_CREATED,
        )
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    serializer = VoterLoginSerializer(data=request.data)
    if serializer.is_valid():
        voter = serializer.validated_data["voter"]
        refresh = RefreshToken.for_user(voter)
        return Response(
            {
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "voter": {
                    "id": voter.id,
                    "voter_code": voter.voter_code,
                    "full_name": voter.full_name,
                    "id_number": voter.id_number,
                    "county": voter.county,
                    "constituency": voter.constituency,
                    "ward": voter.ward,
                },
            },
            status=status.HTTP_200_OK,
        )
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── Authenticated endpoints ───────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def seats_for_voter(request):
    """Return only the seats a voter is eligible to vote for based on their
    registered county / constituency / ward."""
    voter = request.user  # Resolved by VoterJWTAuthentication

    seats = Seat.objects.filter(
        Q(level="National")
        | Q(level="County", county=voter.county)
        | Q(level="Constituency", constituency=voter.constituency)
        | Q(level="Ward", ward=voter.ward)
    )

    # Attach which seats the voter already voted on.
    voted_seat_ids = set(
        Vote.objects.filter(voter=voter).values_list("seat_id", flat=True)
    )

    data = SeatSerializer(seats, many=True).data
    for seat in data:
        seat["has_voted"] = seat["id"] in voted_seat_ids

    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def candidates_for_seat(request, seat_id):
    """Return all candidates running for a specific seat."""
    candidates = Candidate.objects.filter(seat_id=seat_id).select_related("seat")
    serializer = CandidateSerializer(candidates, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cast_vote(request):
    """Cast a vote.  Expects { "seat": <id>, "candidate": <id> }.

    • The serializer's validate() ensures the candidate belongs to the seat.
    • The creation is wrapped in transaction.atomic() so the INSERT + any
      future side-effects are all-or-nothing.
    • If the DB UniqueConstraint fires (race condition between two
      concurrent requests), the IntegrityError is caught and a clear
      400 is returned instead of a 500.
    """
    voter = request.user

    serializer = VoteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            serializer.save(voter=voter)
    except IntegrityError:
        return Response(
            {"error": "You have already cast a vote for this seat."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {"message": "Vote cast successfully"}, status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vote_results(request):
    """Aggregated vote counts per candidate, with optional filters.

    Query parameters (all optional, combinable):
        seat_type   – e.g. president, governor, senator, mp, woman_rep, mca
        county      – e.g. Nairobi
        constituency – e.g. Westlands
        ward        – e.g. Kitisuru

    The annotation is done on Candidate → votes (reverse FK), so candidates
    with zero votes are still included (vote_count = 0).
    Results are ordered by seat then descending vote count.
    """
    qs = Candidate.objects.select_related("seat")

    # ── Optional filters ──────────────────────────────────────────
    seat_type = request.query_params.get("seat_type")
    county = request.query_params.get("county")
    constituency = request.query_params.get("constituency")
    ward = request.query_params.get("ward")

    if seat_type:
        qs = qs.filter(seat__seat_type=seat_type)
    if county:
        qs = qs.filter(Q(seat__county=county) | Q(seat__level="National"))
    if constituency:
        qs = qs.filter(seat__constituency=constituency)
    if ward:
        qs = qs.filter(seat__ward=ward)

    # ── Annotate & order ──────────────────────────────────────────
    qs = (
        qs.values(
            "id",
            "full_name",
            "party",
            "photo_url",
            "seat__id",
            "seat__seat_type",
            "seat__name",
            "seat__level",
        )
        .annotate(vote_count=Count("votes"))
        .order_by("seat__id", "-vote_count")
    )

    data = [
        {
            "candidate_id": r["id"],
            "candidate_name": r["full_name"],
            "party": r["party"],
            "photo_url": r["photo_url"],
            "seat_id": r["seat__id"],
            "seat_type": r["seat__seat_type"],
            "seat_name": r["seat__name"],
            "seat_level": r["seat__level"],
            "vote_count": r["vote_count"],
        }
        for r in qs
    ]

    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def voter_votes(request):
    """Return the list of seat IDs the authenticated voter has already voted on."""
    voted = Vote.objects.filter(voter=request.user).values_list("seat_id", flat=True)
    return Response(list(voted))


    
