from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import VoterRegistrationSerializer, VoterLoginSerializer


@api_view(["GET"])
def index(request):
    return Response("Hello Timo")


@api_view(["POST"])
def signup(request):
    serializer = VoterRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        voter = serializer.save()
        return Response(
            {
                "message": "Registration successful",
                "voter_code": voter.voter_code,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {"errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
def login(request):
    """Authenticate a voter by id_number + password and return JWT tokens."""
    serializer = VoterLoginSerializer(data=request.data)

    if serializer.is_valid():
        voter = serializer.validated_data["voter"]

        # Issue JWT pair for this voter.
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

    return Response(
        {"errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


    
