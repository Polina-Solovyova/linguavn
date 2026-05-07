"""DRF serializers for the novels app."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import (
    Achievement,
    Novel,
    QuizAttempt,
    QuizChoice,
    QuizQuestion,
    Quiz,
    UserAchievement,
    UserProfile,
    UserProgress,
    UserVocabulary,
    VocabularyWord,
)

User = get_user_model()


class UserRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = (
            "username",
            "email",
            "avatar",
            "diamonds",
            "language_level",
            "genre_preferences",
            "total_score",
            "streak_days",
            "last_activity",
        )

    def get_avatar(self, obj: UserProfile) -> str | None:
        request = self.context.get("request")
        if not obj.avatar:
            return None
        url = obj.avatar.url
        return request.build_absolute_uri(url) if request else url


class UserProfileUpdateSerializer(serializers.Serializer):
    language_level = serializers.ChoiceField(
        choices=["B1", "B2", "C1"], required=False
    )
    genre_preferences = serializers.ListField(
        child=serializers.CharField(max_length=64),
        required=False,
    )


class NovelSerializer(serializers.ModelSerializer):
    cover_image = serializers.SerializerMethodField()
    scenario_url = serializers.SerializerMethodField()
    vocabulary_count = serializers.SerializerMethodField()
    quiz_count = serializers.SerializerMethodField()

    class Meta:
        model = Novel
        fields = (
            "id",
            "title",
            "description",
            "cover_image",
            "scenario_url",
            "language_level",
            "genre",
            "estimated_minutes",
            "vocabulary_count",
            "quiz_count",
            "created_at",
        )

    def _absolute(self, url: str | None) -> str | None:
        if not url:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def get_cover_image(self, obj: Novel) -> str | None:
        return self._absolute(obj.cover_image.url if obj.cover_image else None)

    def get_scenario_url(self, obj: Novel) -> str | None:
        return self._absolute(obj.scenario_file.url if obj.scenario_file else None)

    def get_vocabulary_count(self, obj: Novel) -> int:
        return obj.vocabulary.count()

    def get_quiz_count(self, obj: Novel) -> int:
        return obj.quizzes.count()


class VocabularyWordSerializer(serializers.ModelSerializer):
    is_learned = serializers.SerializerMethodField()

    class Meta:
        model = VocabularyWord
        fields = (
            "id",
            "word",
            "translation",
            "transcription",
            "definition",
            "example",
            "level",
            "is_learned",
        )

    def get_is_learned(self, obj: VocabularyWord) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        profile = getattr(request, "_profile_cache", None)
        if profile is None:
            try:
                profile = request.user.profile
                request._profile_cache = profile
            except Exception:
                return False
        return UserVocabulary.objects.filter(user=profile, word=obj).exists()


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ("id", "code", "title", "description", "icon", "points")


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = UserAchievement
        fields = ("id", "achievement", "earned_at")


class QuizChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizChoice
        fields = ("id", "text")


class QuizChoiceWithAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizChoice
        fields = ("id", "text", "is_correct", "explanation")


class QuizQuestionSerializer(serializers.ModelSerializer):
    choices = QuizChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ("id", "text", "question_type", "hint", "order", "choices")


class QuizQuestionWithAnswersSerializer(serializers.ModelSerializer):
    choices = QuizChoiceWithAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ("id", "text", "question_type", "hint", "order", "choices")


class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ("id", "chapter_node_id", "title", "pass_threshold", "questions")


class QuizSubmitSerializer(serializers.Serializer):
    answers = serializers.DictField(
        child=serializers.ListField(child=serializers.IntegerField()),
        help_text="Map of question_id -> [selected choice_id, ...]",
    )


class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz_id = serializers.IntegerField(source="quiz.id", read_only=True)
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = (
            "id",
            "quiz_id",
            "quiz_title",
            "score",
            "max_score",
            "passed",
            "answers",
            "completed_at",
        )


class UserProgressSerializer(serializers.ModelSerializer):
    novel_id = serializers.IntegerField(source="novel.id", read_only=True)
    novel_title = serializers.CharField(source="novel.title", read_only=True)

    class Meta:
        model = UserProgress
        fields = (
            "novel_id",
            "novel_title",
            "current_node_id",
            "state_snapshot",
            "visited_nodes",
            "is_completed",
            "progress_percent",
            "current_level",
            "correct_count",
            "error_count",
            "updated_at",
        )


class ProgressUpdateSerializer(serializers.Serializer):
    current_node_id = serializers.CharField(max_length=128)
    state_snapshot = serializers.DictField(required=False, default=dict)
    visited_nodes = serializers.ListField(
        child=serializers.CharField(max_length=128), required=False, default=list
    )
    is_completed = serializers.BooleanField(required=False, default=False)
    progress_percent = serializers.FloatField(required=False, default=0.0)
    current_level = serializers.ChoiceField(
        choices=["B1", "B2", "C1"], required=False, default="B1"
    )
    correct_count = serializers.IntegerField(required=False, default=0, min_value=0)
    error_count = serializers.IntegerField(required=False, default=0, min_value=0)

    def validate_progress_percent(self, value: float) -> float:
        if not 0.0 <= value <= 100.0:
            raise serializers.ValidationError(
                "progress_percent must be between 0 and 100."
            )
        return value
