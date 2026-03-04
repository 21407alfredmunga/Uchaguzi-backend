"""
Custom JWT authentication backend for the Voter model.

SimpleJWT's default JWTAuthentication resolves tokens against
settings.AUTH_USER_MODEL (django.contrib.auth.User).  Since Voter is a
standalone model, we override the user-lookup step so that incoming
Bearer tokens are resolved against the Voter table instead.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings

from .models import Voter


class VoterJWTAuthentication(JWTAuthentication):
    """Authenticate requests by looking up the Voter whose PK is stored in
    the JWT's ``voter_id`` claim (configured via SIMPLE_JWT.USER_ID_CLAIM)."""

    def get_user(self, validated_token):
        try:
            voter_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            from rest_framework_simplejwt.exceptions import InvalidToken
            raise InvalidToken("Token contained no recognisable voter identification")

        try:
            return Voter.objects.get(**{api_settings.USER_ID_FIELD: voter_id})
        except Voter.DoesNotExist:
            from rest_framework_simplejwt.exceptions import AuthenticationFailed
            raise AuthenticationFailed("Voter not found")
