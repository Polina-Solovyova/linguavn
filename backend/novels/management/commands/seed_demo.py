"""Seed the database with a demo novel built programmatically.

Usage:
    python manage.py seed_demo

This command (re)creates a single Novel record pointing to a JSON
scenario produced by the Python builder in `vn_builder`. It is safe
to re-run: an existing demo novel is updated in place.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from novels.models import Novel


# Make the local builder importable when running inside the container.
BACKEND_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "vn-builder" / "python"))

from vn_builder import build_demo_scenario  # noqa: E402  (path injection)


class Command(BaseCommand):
    help = "Create or refresh the demo Novel from the programmatic builder."

    DEMO_TITLE = "Demo: A Walk Through Tokyo"

    def handle(self, *args, **options):
        scenario = build_demo_scenario()
        payload = json.dumps(scenario, ensure_ascii=False, indent=2).encode("utf-8")

        novel, created = Novel.objects.get_or_create(
            title=self.DEMO_TITLE,
            defaults={
                "description": (
                    "A small branching scene built programmatically with the "
                    "vn_builder API to verify the end-to-end pipeline."
                ),
            },
        )
        if not created:
            novel.description = (
                "A small branching scene built programmatically with the "
                "vn_builder API to verify the end-to-end pipeline."
            )

        filename = "demo_walk_through_tokyo.json"
        novel.scenario_file.save(filename, ContentFile(payload), save=False)
        novel.is_published = True
        novel.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"{'Created' if created else 'Updated'} demo novel id={novel.id}"
            )
        )
