"""
Management command to seed the Seat table with Kenya's electoral structure.

Usage:
    python manage.py seed_seats
"""

from django.core.management.base import BaseCommand

from voting_api.models import Seat


# ── Kenya's 47 counties ──────────────────────────────────────────────

COUNTIES = [
    "Mombasa",
    "Kwale",
    "Kilifi",
    "Tana River",
    "Lamu",
    "Taita-Taveta",
    "Garissa",
    "Wajir",
    "Mandera",
    "Marsabit",
    "Isiolo",
    "Meru",
    "Tharaka-Nithi",
    "Embu",
    "Kitui",
    "Machakos",
    "Makueni",
    "Nyandarua",
    "Nyeri",
    "Kirinyaga",
    "Murang'a",
    "Kiambu",
    "Turkana",
    "West Pokot",
    "Samburu",
    "Trans-Nzoia",
    "Uasin Gishu",
    "Elgeyo-Marakwet",
    "Nandi",
    "Baringo",
    "Laikipia",
    "Nakuru",
    "Narok",
    "Kajiado",
    "Kericho",
    "Bomet",
    "Kakamega",
    "Vihiga",
    "Bungoma",
    "Busia",
    "Siaya",
    "Kisumu",
    "Homa Bay",
    "Migori",
    "Kisii",
    "Nyamira",
    "Nairobi",
]

# ── Sample constituencies for Nairobi & Mombasa ─────────────────────

SAMPLE_CONSTITUENCIES: dict[str, list[str]] = {
    "Nairobi": [
        "Westlands",
        "Dagoretti North",
        "Dagoretti South",
        "Langata",
        "Kibra",
        "Roysambu",
        "Kasarani",
        "Starehe",
        "Mathare",
        "Embakasi South",
        "Embakasi North",
        "Embakasi Central",
        "Embakasi East",
        "Embakasi West",
        "Makadara",
        "Kamukunji",
        "Ruaraka",
    ],
    "Mombasa": [
        "Changamwe",
        "Jomvu",
        "Kisauni",
        "Nyali",
        "Likoni",
        "Mvita",
    ],
}

# ── Sample wards (constituency ➜ wards) ─────────────────────────────

SAMPLE_WARDS: dict[str, dict[str, list[str]]] = {
    "Nairobi": {
        "Westlands": [
            "Kitisuru",
            "Parklands/Highridge",
            "Karura",
            "Kangemi",
            "Mountain View",
        ],
        "Langata": [
            "Karen",
            "Nairobi West",
            "Mugumu-Ini",
            "South C",
            "Nyayo Highrise",
        ],
        "Starehe": [
            "Nairobi Central",
            "Ngara",
            "Pangani",
            "Ziwani/Kariokor",
            "Landimawe",
            "Nairobi South",
        ],
    },
    "Mombasa": {
        "Mvita": [
            "Mji wa Kale/Makadara",
            "Tudor",
            "Tononoka",
            "Shimanzi/Ganjoni",
            "Majengo",
        ],
        "Nyali": [
            "Frere Town",
            "Ziwa la Ng'ombe",
            "Mkomani",
            "Kongowea",
            "Kadzandani",
        ],
    },
}

# ── Icons per seat type ──────────────────────────────────────────────

SEAT_ICONS: dict[str, str] = {
    "president": "🇰🇪",
    "governor": "🏛️",
    "senator": "⚖️",
    "mp": "📋",
    "woman_rep": "👩",
    "mca": "🏘️",
}


class Command(BaseCommand):
    help = "Seed the Seat table with Kenya's 47 counties, sample constituencies and wards."

    def handle(self, *args, **options):
        created_total = 0

        # ── 1. National-level seat: President ────────────────────
        _, created = Seat.objects.get_or_create(
            seat_type="president",
            county=None,
            constituency=None,
            ward=None,
            defaults={
                "name": "President of Kenya",
                "level": "National",
                "icon": SEAT_ICONS["president"],
            },
        )
        if created:
            created_total += 1
        self.stdout.write(self._tag(created) + " President")

        # ── 2. County-level seats (Governor, Senator, Woman Rep) ─
        for county in COUNTIES:
            for seat_type in ("governor", "senator", "woman_rep"):
                label = dict(Seat.SEAT_TYPES)[seat_type]
                name = f"{county} {label}"
                _, created = Seat.objects.get_or_create(
                    seat_type=seat_type,
                    county=county,
                    constituency=None,
                    ward=None,
                    defaults={
                        "name": name,
                        "level": "County",
                        "icon": SEAT_ICONS[seat_type],
                    },
                )
                if created:
                    created_total += 1
                self.stdout.write(self._tag(created) + f" {name}")

        # ── 3. Constituency-level seats (MP) ─────────────────────
        for county, constituencies in SAMPLE_CONSTITUENCIES.items():
            for constituency in constituencies:
                name = f"{constituency} MP"
                _, created = Seat.objects.get_or_create(
                    seat_type="mp",
                    county=county,
                    constituency=constituency,
                    ward=None,
                    defaults={
                        "name": name,
                        "level": "Constituency",
                        "icon": SEAT_ICONS["mp"],
                    },
                )
                if created:
                    created_total += 1
                self.stdout.write(self._tag(created) + f" {name}")

        # ── 4. Ward-level seats (MCA) ────────────────────────────
        for county, const_map in SAMPLE_WARDS.items():
            for constituency, wards in const_map.items():
                for ward in wards:
                    name = f"{ward} MCA"
                    _, created = Seat.objects.get_or_create(
                        seat_type="mca",
                        county=county,
                        constituency=constituency,
                        ward=ward,
                        defaults={
                            "name": name,
                            "level": "Ward",
                            "icon": SEAT_ICONS["mca"],
                        },
                    )
                    if created:
                        created_total += 1
                    self.stdout.write(self._tag(created) + f" {name}")

        # ── Summary ──────────────────────────────────────────────
        total = Seat.objects.count()
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {created_total} new seat(s) created. "
                f"{total} total seat(s) in the database."
            )
        )

    # helper
    def _tag(self, created: bool) -> str:
        if created:
            return self.style.SUCCESS("  [CREATED]")
        return self.style.WARNING("  [EXISTS] ")
