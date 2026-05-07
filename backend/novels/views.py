"""HTTP views for the novels app."""

from __future__ import annotations

import logging

from django.contrib.auth import authenticate
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Achievement,
    Novel,
    Quiz,
    QuizAttempt,
    UserAchievement,
    UserProfile,
    UserProgress,
    UserVocabulary,
    VocabularyWord,
)
from .serializers import (
    AchievementSerializer,
    NovelSerializer,
    ProgressUpdateSerializer,
    QuizAttemptSerializer,
    QuizSerializer,
    QuizSubmitSerializer,
    UserAchievementSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserProgressSerializer,
    UserRegisterSerializer,
    VocabularyWordSerializer,
)

logger = logging.getLogger(__name__)


def _tokens_for(user) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def _user_payload(user) -> dict:
    return {"id": user.id, "username": user.username, "email": user.email}


def _get_profile(request) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return profile


# Authentication

@swagger_auto_schema(method="post", request_body=UserRegisterSerializer)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    tokens = _tokens_for(user)
    return Response(
        {"user": _user_payload(user), **tokens},
        status=status.HTTP_201_CREATED,
    )


@swagger_auto_schema(method="post", request_body=UserLoginSerializer)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(
        username=serializer.validated_data["username"],
        password=serializer.validated_data["password"],
    )
    if user is None:
        return Response(
            {"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED
        )
    tokens = _tokens_for(user)
    return Response({"user": _user_payload(user), **tokens})


@swagger_auto_schema(method="post")
@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token_view(request):
    raw = request.data.get("refresh")
    if not raw:
        return Response(
            {"detail": "refresh token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        refresh = RefreshToken(raw)
        access = str(refresh.access_token)
    except (InvalidToken, TokenError) as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({"access": access})


@swagger_auto_schema(method="post")
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    raw = request.data.get("refresh")
    if raw:
        try:
            RefreshToken(raw).set_jti()
        except Exception:
            logger.debug("Refresh token blacklist skipped.")
    return Response({"detail": "Logged out."})


# Profile

@swagger_auto_schema(method="get")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    profile = _get_profile(request)
    profile.update_streak()
    progress = UserProgress.objects.filter(user=profile).select_related("novel")
    achievements = UserAchievement.objects.filter(user=profile).select_related(
        "achievement"
    )
    quiz_attempts = QuizAttempt.objects.filter(user=profile).select_related(
        "quiz", "quiz__novel"
    ).order_by("-completed_at")[:20]
    learned_count = UserVocabulary.objects.filter(user=profile).count()

    return Response(
        {
            "profile": UserProfileSerializer(
                profile, context={"request": request}
            ).data,
            "progress": UserProgressSerializer(progress, many=True).data,
            "achievements": UserAchievementSerializer(achievements, many=True).data,
            "quiz_attempts": QuizAttemptSerializer(quiz_attempts, many=True).data,
            "learned_words_count": learned_count,
        }
    )


@swagger_auto_schema(method="patch", request_body=UserProfileUpdateSerializer)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def profile_update(request):
    profile = _get_profile(request)
    serializer = UserProfileUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    if "language_level" in data:
        profile.language_level = data["language_level"]
    if "genre_preferences" in data:
        profile.genre_preferences = data["genre_preferences"]
    profile.save()
    return Response(
        UserProfileSerializer(profile, context={"request": request}).data
    )


@swagger_auto_schema(method="post")
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_avatar(request):
    avatar = request.FILES.get("avatar")
    if avatar is None:
        return Response(
            {"detail": "Field 'avatar' is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    profile = _get_profile(request)
    profile.avatar = avatar
    profile.save(update_fields=["avatar"])
    return Response(
        UserProfileSerializer(profile, context={"request": request}).data
    )


# Novels

@swagger_auto_schema(method="get", responses={200: NovelSerializer(many=True)})
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def novel_list(request):
    qs = Novel.objects.filter(is_published=True)
    level = request.query_params.get("level")
    genre = request.query_params.get("genre")
    if level and level in ("B1", "B2", "C1"):
        qs = qs.filter(language_level=level)
    if genre:
        qs = qs.filter(genre__icontains=genre)
    return Response(
        NovelSerializer(qs, many=True, context={"request": request}).data
    )


@swagger_auto_schema(method="get", responses={200: NovelSerializer()})
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def novel_detail(request, novel_id: int):
    novel = get_object_or_404(Novel, id=novel_id, is_published=True)
    return Response(NovelSerializer(novel, context={"request": request}).data)


# Progress

@swagger_auto_schema(method="get")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def progress_get(request, novel_id: int):
    novel = get_object_or_404(Novel, id=novel_id, is_published=True)
    profile = _get_profile(request)
    progress, _ = UserProgress.objects.get_or_create(user=profile, novel=novel)
    return Response(UserProgressSerializer(progress).data)


@swagger_auto_schema(method="put", request_body=ProgressUpdateSerializer)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def progress_update(request, novel_id: int):
    novel = get_object_or_404(Novel, id=novel_id, is_published=True)
    profile = _get_profile(request)

    serializer = ProgressUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    progress, _ = UserProgress.objects.get_or_create(user=profile, novel=novel)
    payload = serializer.validated_data
    progress.current_node_id = payload["current_node_id"]
    progress.state_snapshot = payload.get("state_snapshot", {})
    progress.visited_nodes = payload.get("visited_nodes", [])
    progress.is_completed = payload.get("is_completed", False)
    progress.progress_percent = payload.get("progress_percent", 0.0)
    progress.current_level = payload.get("current_level", "B1")
    progress.correct_count = payload.get("correct_count", 0)
    progress.error_count = payload.get("error_count", 0)
    progress.save()

    if progress.is_completed:
        _check_completion_achievement(profile, novel)

    if len(progress.visited_nodes) >= 5:
        _award_achievement(profile, "first_choice")

    return Response(UserProgressSerializer(progress).data)


@swagger_auto_schema(method="post")
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def progress_reset(request, novel_id: int):
    novel = get_object_or_404(Novel, id=novel_id, is_published=True)
    profile = _get_profile(request)
    UserProgress.objects.filter(user=profile, novel=novel).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Vocabulary

@swagger_auto_schema(method="get")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vocabulary_list(request, novel_id: int):
    novel = get_object_or_404(Novel, id=novel_id, is_published=True)
    words = VocabularyWord.objects.filter(novel=novel)
    level = request.query_params.get("level")
    if level and level in ("B1", "B2", "C1"):
        words = words.filter(level=level)
    return Response(
        VocabularyWordSerializer(
            words, many=True, context={"request": request}
        ).data
    )


@swagger_auto_schema(method="post")
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def vocabulary_learn(request, word_id: int):
    word = get_object_or_404(VocabularyWord, id=word_id)
    profile = _get_profile(request)
    _, created = UserVocabulary.objects.get_or_create(user=profile, word=word)
    if created:
        profile.add_score(2)
        _check_vocab_achievement(profile)
    return Response(
        VocabularyWordSerializer(word, context={"request": request}).data
    )


@swagger_auto_schema(method="delete")
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def vocabulary_forget(request, word_id: int):
    word = get_object_or_404(VocabularyWord, id=word_id)
    profile = _get_profile(request)
    UserVocabulary.objects.filter(user=profile, word=word).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Quiz

@swagger_auto_schema(method="get")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quiz_for_novel(request, novel_id: int):
    novel = get_object_or_404(Novel, id=novel_id, is_published=True)
    quizzes = Quiz.objects.filter(novel=novel).prefetch_related(
        "questions", "questions__choices"
    )
    return Response(QuizSerializer(quizzes, many=True).data)


@swagger_auto_schema(method="get")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quiz_detail(request, quiz_id: int):
    quiz = get_object_or_404(
        Quiz.objects.prefetch_related("questions", "questions__choices"),
        id=quiz_id,
    )
    return Response(QuizSerializer(quiz).data)


@swagger_auto_schema(method="post", request_body=QuizSubmitSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def quiz_submit(request, quiz_id: int):
    quiz = get_object_or_404(
        Quiz.objects.prefetch_related("questions", "questions__choices"),
        id=quiz_id,
    )
    profile = _get_profile(request)

    serializer = QuizSubmitSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user_answers: dict[str, list[int]] = serializer.validated_data["answers"]

    score = 0.0
    max_score = 0.0
    result_details: dict[str, dict] = {}

    for question in quiz.questions.all():
        qid = str(question.id)
        max_score += 1.0
        correct_ids = set(
            question.choices.filter(is_correct=True).values_list("id", flat=True)
        )
        selected_ids = set(user_answers.get(qid, []))
        is_correct = selected_ids == correct_ids and bool(correct_ids)
        if is_correct:
            score += 1.0

        explanations = {}
        for choice in question.choices.all():
            if choice.explanation:
                explanations[choice.id] = choice.explanation

        result_details[qid] = {
            "correct": is_correct,
            "correct_ids": list(correct_ids),
            "selected_ids": list(selected_ids),
            "explanations": explanations,
        }

    passed = max_score > 0 and (score / max_score) >= quiz.pass_threshold

    with transaction.atomic():
        attempt = QuizAttempt.objects.create(
            user=profile,
            quiz=quiz,
            score=score,
            max_score=max_score,
            passed=passed,
            answers=result_details,
        )
        if passed:
            profile.add_score(int(score * 10))
            _check_quiz_achievement(profile)

        # Update progress error/correct counts for adaptation
        try:
            progress = UserProgress.objects.get(user=profile, novel=quiz.novel)
            if passed:
                progress.correct_count += int(score)
            else:
                progress.error_count += int(max_score - score)
            progress.save(update_fields=["correct_count", "error_count"])
        except UserProgress.DoesNotExist:
            pass

    return Response(
        {
            "attempt": QuizAttemptSerializer(attempt).data,
            "details": result_details,
        },
        status=status.HTTP_201_CREATED,
    )


@swagger_auto_schema(method="get")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quiz_attempts(request, quiz_id: int):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    profile = _get_profile(request)
    attempts = QuizAttempt.objects.filter(user=profile, quiz=quiz).order_by(
        "-completed_at"
    )
    return Response(QuizAttemptSerializer(attempts, many=True).data)


# Achievements

@swagger_auto_schema(method="get")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def achievements_list(request):
    all_achievements = Achievement.objects.all()
    profile = _get_profile(request)
    earned_codes = set(
        UserAchievement.objects.filter(user=profile).values_list(
            "achievement__code", flat=True
        )
    )
    data = []
    for ach in all_achievements:
        item = AchievementSerializer(ach).data
        item["earned"] = ach.code in earned_codes
        data.append(item)
    return Response(data)


@swagger_auto_schema(method="get")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_achievements(request):
    profile = _get_profile(request)
    earned = UserAchievement.objects.filter(user=profile).select_related("achievement")
    return Response(UserAchievementSerializer(earned, many=True).data)


# Stats

@swagger_auto_schema(method="get")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_stats(request):
    profile = _get_profile(request)
    completed = UserProgress.objects.filter(user=profile, is_completed=True).count()
    in_progress = UserProgress.objects.filter(
        user=profile, is_completed=False, progress_percent__gt=0
    ).count()
    learned_words = UserVocabulary.objects.filter(user=profile).count()
    quizzes_passed = QuizAttempt.objects.filter(user=profile, passed=True).count()
    achievements_count = UserAchievement.objects.filter(user=profile).count()

    return Response(
        {
            "novels_completed": completed,
            "novels_in_progress": in_progress,
            "words_learned": learned_words,
            "quizzes_passed": quizzes_passed,
            "achievements_count": achievements_count,
            "total_score": profile.total_score,
            "streak_days": profile.streak_days,
            "language_level": profile.language_level,
        }
    )


# Internal achievement helpers

def _award_achievement(profile: UserProfile, code: str) -> None:
    try:
        ach = Achievement.objects.get(code=code)
        _, created = UserAchievement.objects.get_or_create(
            user=profile, achievement=ach
        )
        if created:
            profile.add_score(ach.points)
            logger.info("Achievement %s awarded to %s", code, profile)
    except Achievement.DoesNotExist:
        pass


def _check_completion_achievement(profile: UserProfile, novel: Novel) -> None:  # noqa: ARG001
    completed_count = UserProgress.objects.filter(
        user=profile, is_completed=True
    ).count()
    if completed_count == 1:
        _award_achievement(profile, "first_novel")
    if completed_count >= 5:
        _award_achievement(profile, "five_novels")


def _check_vocab_achievement(profile: UserProfile) -> None:
    count = UserVocabulary.objects.filter(user=profile).count()
    if count >= 5:
        _award_achievement(profile, "vocab_5")
    if count >= 10:
        _award_achievement(profile, "vocab_10")
    if count >= 50:
        _award_achievement(profile, "vocab_50")


def _check_quiz_achievement(profile: UserProfile) -> None:
    passed = QuizAttempt.objects.filter(user=profile, passed=True).count()
    if passed == 1:
        _award_achievement(profile, "first_quiz")
    if passed >= 10:
        _award_achievement(profile, "quiz_master")
