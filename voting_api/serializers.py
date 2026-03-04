import string
import secrets

from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password

from .models import Voter


def generate_voter_code(length=8):
    """Generate a unique alphanumeric voter code."""
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(length))
        if not Voter.objects.filter(voter_code=code).exists():
            return code


class VoterRegistrationSerializer(serializers.ModelSerializer):
    # Accept a plain-text password from the client; write-only so it never
    # appears in responses.
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Voter
        fields = [
            "full_name",
            "id_number",
            "phone_number",
            "email",
            "county",
            "constituency",
            "ward",
            "password",
        ]

    def create(self, validated_data):
        # Pop the plain-text password — it doesn't map to a model field.
        raw_password = validated_data.pop("password")

        # Auto-generate a unique voter code.
        validated_data["voter_code"] = generate_voter_code()

        # Hash the password before persisting.
        validated_data["password_hash"] = make_password(raw_password)

        return super().create(validated_data)


# ---------------------------------------------------------------------------
# Login serializer — validates credentials & returns JWT tokens
# ---------------------------------------------------------------------------
class VoterLoginSerializer(serializers.Serializer):
    """Accept id_number + password, authenticate against the Voter table,
    and return access / refresh tokens."""

    id_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        id_number = attrs["id_number"].strip()
        password = attrs["password"]

        try:
            voter = Voter.objects.get(id_number=id_number)
        except Voter.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials.")

        if not check_password(password, voter.password_hash):
            raise serializers.ValidationError("Invalid credentials.")

        # Stash the voter instance so the view can access it.
        attrs["voter"] = voter
        return attrs
