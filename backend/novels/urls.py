"""URL routing for the novels API."""

from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    # Authentication
    path("auth/register/", views.register, name="auth-register"),
    path("auth/login/", views.login_view, name="auth-login"),
    path("auth/logout/", views.logout_view, name="auth-logout"),
    path("auth/refresh/", views.refresh_token_view, name="auth-refresh"),

    # Profile
    path("profile/", views.profile_view, name="profile"),
    path("profile/update/", views.profile_update, name="profile-update"),
    path("profile/avatar/", views.upload_avatar, name="profile-avatar"),
    path("profile/stats/", views.user_stats, name="profile-stats"),
    path("profile/achievements/", views.user_achievements, name="profile-achievements"),

    # Novels
    path("novels/", views.novel_list, name="novel-list"),
    path("novels/<int:novel_id>/", views.novel_detail, name="novel-detail"),

    # Progress
    path("novels/<int:novel_id>/progress/", views.progress_get, name="progress-get"),
    path("novels/<int:novel_id>/progress/update/", views.progress_update, name="progress-update"),
    path("novels/<int:novel_id>/progress/reset/", views.progress_reset, name="progress-reset"),

    # Vocabulary
    path("novels/<int:novel_id>/vocabulary/", views.vocabulary_list, name="vocabulary-list"),
    path("vocabulary/<int:word_id>/learn/", views.vocabulary_learn, name="vocabulary-learn"),
    path("vocabulary/<int:word_id>/forget/", views.vocabulary_forget, name="vocabulary-forget"),

    # Quiz
    path("novels/<int:novel_id>/quizzes/", views.quiz_for_novel, name="quiz-list"),
    path("quizzes/<int:quiz_id>/", views.quiz_detail, name="quiz-detail"),
    path("quizzes/<int:quiz_id>/submit/", views.quiz_submit, name="quiz-submit"),
    path("quizzes/<int:quiz_id>/attempts/", views.quiz_attempts, name="quiz-attempts"),

    # Achievements
    path("achievements/", views.achievements_list, name="achievements-list"),
]
