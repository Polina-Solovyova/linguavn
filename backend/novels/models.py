"""Domain models for the educational visual novel platform.

The scenario content lives in JSON scenario files (compatible with
vn-builder and the JS runtime). DB models handle users, progress,
educational features (vocabulary, quizzes, achievements) and
rule-based difficulty adaptation.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

User = get_user_model()

LANGUAGE_LEVELS = [("B1", "B1"), ("B2", "B2"), ("C1", "C1")]


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        default="avatars/default_avatar.png",
        blank=True,
    )
    diamonds = models.PositiveIntegerField(default=0)
    language_level = models.CharField(
        max_length=2, choices=LANGUAGE_LEVELS, default="B1"
    )
    genre_preferences = models.JSONField(default=list, blank=True)
    total_score = models.PositiveIntegerField(default=0)
    streak_days = models.PositiveIntegerField(default=0)
    last_activity = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return self.user.username

    def update_streak(self) -> None:
        today = timezone.localdate()
        if self.last_activity is None:
            self.streak_days = 1
        elif self.last_activity == today:
            return
        elif (today - self.last_activity).days == 1:
            self.streak_days += 1
        else:
            self.streak_days = 1
        self.last_activity = today
        self.save(update_fields=["streak_days", "last_activity"])

    def add_score(self, points: int) -> None:
        if points > 0:
            self.total_score = models.F("total_score") + points
            self.save(update_fields=["total_score"])
            self.refresh_from_db(fields=["total_score"])


@receiver(post_save, sender=User)
def _create_user_profile(sender, instance, created, **kwargs) -> None:
    if created:
        UserProfile.objects.create(user=instance)


class Novel(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="novels/covers/", blank=True)
    scenario_file = models.FileField(upload_to="scenarios/")
    is_published = models.BooleanField(default=True)
    language_level = models.CharField(
        max_length=2, choices=LANGUAGE_LEVELS, default="B1"
    )
    genre = models.CharField(max_length=64, blank=True)
    estimated_minutes = models.PositiveSmallIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title


class VocabularyWord(models.Model):
    novel = models.ForeignKey(
        Novel, on_delete=models.CASCADE, related_name="vocabulary"
    )
    word = models.CharField(max_length=128)
    translation = models.CharField(max_length=256, blank=True)
    transcription = models.CharField(max_length=128, blank=True)
    definition = models.TextField(blank=True)
    example = models.TextField(blank=True)
    level = models.CharField(max_length=2, choices=LANGUAGE_LEVELS, default="B1")

    class Meta:
        ordering = ("word",)

    def __str__(self) -> str:
        return f"{self.word} ({self.novel})"


class Achievement(models.Model):
    code = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=64, blank=True)
    points = models.PositiveSmallIntegerField(default=10)

    def __str__(self) -> str:
        return self.title


class Quiz(models.Model):
    novel = models.ForeignKey(
        Novel, on_delete=models.CASCADE, related_name="quizzes"
    )
    chapter_node_id = models.CharField(max_length=128)
    title = models.CharField(max_length=255, blank=True)
    pass_threshold = models.FloatField(default=0.6)

    def __str__(self) -> str:
        return f"{self.novel} — quiz at {self.chapter_node_id}"


class QuizQuestion(models.Model):
    TYPES = [
        ("single", "Single choice"),
        ("multiple", "Multiple choice"),
        ("fill", "Fill in the blank"),
    ]
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="questions"
    )
    text = models.TextField()
    question_type = models.CharField(max_length=16, choices=TYPES, default="single")
    hint = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("order",)

    def __str__(self) -> str:
        return self.text[:80]


class QuizChoice(models.Model):
    question = models.ForeignKey(
        QuizQuestion, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(blank=True)

    def __str__(self) -> str:
        marker = "✓" if self.is_correct else "✗"
        return f"{marker} {self.text[:60]}"


class QuizAttempt(models.Model):
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="attempts"
    )
    score = models.FloatField(default=0.0)
    max_score = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)
    answers = models.JSONField(default=dict)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user} on {self.quiz}: {self.score}/{self.max_score}"


class UserAchievement(models.Model):
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="achievements"
    )
    achievement = models.ForeignKey(
        Achievement, on_delete=models.CASCADE, related_name="earned_by"
    )
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "achievement")

    def __str__(self) -> str:
        return f"{self.user} — {self.achievement}"


class UserVocabulary(models.Model):
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="learned_words"
    )
    word = models.ForeignKey(
        VocabularyWord, on_delete=models.CASCADE, related_name="learned_by"
    )
    learned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "word")

    def __str__(self) -> str:
        return f"{self.user} → {self.word.word}"


class UserProgress(models.Model):
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="progress_entries"
    )
    novel = models.ForeignKey(
        Novel, on_delete=models.CASCADE, related_name="progress_entries"
    )
    current_node_id = models.CharField(max_length=128, blank=True)
    state_snapshot = models.JSONField(default=dict, blank=True)
    visited_nodes = models.JSONField(default=list, blank=True)
    is_completed = models.BooleanField(default=False)
    progress_percent = models.FloatField(default=0.0)
    current_level = models.CharField(
        max_length=2, choices=LANGUAGE_LEVELS, default="B1"
    )
    correct_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "novel"), name="unique_user_novel_progress"
            )
        ]
        ordering = ("-updated_at",)

    def __str__(self) -> str:
        return f"{self.user} · {self.novel} · {self.progress_percent:.0f}%"
