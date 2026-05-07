"""Smoke tests for the API."""
from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Novel, UserProfile

User = get_user_model()


def _make_scenario() -> bytes:
    return json.dumps(
        {
            "version": "1.0",
            "meta": {"title": "T"},
            "start": "n0",
            "nodes": [
                {"id": "n0", "type": "say", "text": "Hello", "next": "n1"},
                {"id": "n1", "type": "end"},
            ],
        }
    ).encode("utf-8")


class AuthFlowTests(TestCase):
    def test_register_login_refresh(self):
        client = APIClient()

        r = client.post(
            "/api/auth/register/",
            {"username": "ann", "email": "a@b.com", "password": "S3cure!pass"},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.content)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)

        r = client.post(
            "/api/auth/login/",
            {"username": "ann", "password": "S3cure!pass"},
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.content)
        access = r.data["access"]
        refresh = r.data["refresh"]

        r = client.post(
            "/api/auth/refresh/", {"refresh": refresh}, format="json"
        )
        self.assertEqual(r.status_code, 200, r.content)
        self.assertIn("access", r.data)

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        r = client.get("/api/profile/")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["profile"]["username"], "ann")


class NovelProgressTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ann", "a@b.com", "S3cure!pass")
        UserProfile.objects.get_or_create(user=self.user)

        self.novel = Novel.objects.create(
            title="N",
            description="d",
        )
        self.novel.scenario_file.save("s.json", ContentFile(_make_scenario()))

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_list_and_detail(self):
        r = self.client.get("/api/novels/")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(len(r.data), 1)

        r = self.client.get(f"/api/novels/{self.novel.id}/")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["title"], "N")
        self.assertTrue(r.data["scenario_url"].endswith(".json"))

    def test_progress_lifecycle(self):
        url_get = f"/api/novels/{self.novel.id}/progress/"
        url_put = f"/api/novels/{self.novel.id}/progress/update/"
        url_reset = f"/api/novels/{self.novel.id}/progress/reset/"

        r = self.client.get(url_get)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["progress_percent"], 0.0)

        r = self.client.put(
            url_put,
            {
                "current_node_id": "n1",
                "visited_nodes": ["n0", "n1"],
                "is_completed": True,
                "progress_percent": 100.0,
            },
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["current_node_id"], "n1")
        self.assertTrue(r.data["is_completed"])

        r = self.client.post(url_reset)
        self.assertEqual(r.status_code, 204)

        r = self.client.get(url_get)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["progress_percent"], 0.0)
