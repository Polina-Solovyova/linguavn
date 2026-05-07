"""Admin registrations."""
from django.contrib import admin

from .models import (
    Achievement,
    Novel,
    Quiz,
    QuizAttempt,
    QuizChoice,
    QuizQuestion,
    UserAchievement,
    UserProfile,
    UserProgress,
    UserVocabulary,
    VocabularyWord,
)


@admin.register(Novel)
class NovelAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "language_level", "genre", "is_published", "created_at")
    list_filter = ("is_published", "language_level", "genre")
    search_fields = ("title",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "language_level", "total_score", "streak_days", "diamonds")
    list_filter = ("language_level",)
    search_fields = ("user__username", "user__email")


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "novel", "progress_percent", "current_level",
        "correct_count", "error_count", "is_completed", "updated_at",
    )
    list_filter = ("is_completed", "current_level")
    search_fields = ("user__user__username", "novel__title")


class QuizChoiceInline(admin.TabularInline):
    model = QuizChoice
    extra = 2


class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 1
    inlines = []


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("id", "novel", "chapter_node_id", "title", "pass_threshold")
    list_filter = ("novel",)
    search_fields = ("novel__title", "chapter_node_id")
    inlines = [QuizQuestionInline]


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "quiz", "text", "question_type", "order")
    list_filter = ("question_type", "quiz__novel")
    inlines = [QuizChoiceInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "quiz", "score", "max_score", "passed", "completed_at")
    list_filter = ("passed",)
    search_fields = ("user__user__username",)


@admin.register(VocabularyWord)
class VocabularyWordAdmin(admin.ModelAdmin):
    list_display = ("id", "word", "novel", "level", "translation")
    list_filter = ("level", "novel")
    search_fields = ("word", "translation")


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "title", "points")
    search_fields = ("code", "title")


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "achievement", "earned_at")
    list_filter = ("achievement",)


@admin.register(UserVocabulary)
class UserVocabularyAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "word", "learned_at")
    search_fields = ("user__user__username", "word__word")
