# Generated migration for educational platform features.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("novels", "0001_initial"),
    ]

    operations = [
        # Extend UserProfile
        migrations.AddField(
            model_name="userprofile",
            name="language_level",
            field=models.CharField(
                choices=[("B1", "B1"), ("B2", "B2"), ("C1", "C1")],
                default="B1",
                max_length=2,
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="genre_preferences",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="total_score",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="streak_days",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="last_activity",
            field=models.DateField(blank=True, null=True),
        ),
        # Extend Novel
        migrations.AddField(
            model_name="novel",
            name="language_level",
            field=models.CharField(
                choices=[("B1", "B1"), ("B2", "B2"), ("C1", "C1")],
                default="B1",
                max_length=2,
            ),
        ),
        migrations.AddField(
            model_name="novel",
            name="genre",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="novel",
            name="estimated_minutes",
            field=models.PositiveSmallIntegerField(default=30),
        ),
        # Extend UserProgress
        migrations.AddField(
            model_name="userprogress",
            name="current_level",
            field=models.CharField(
                choices=[("B1", "B1"), ("B2", "B2"), ("C1", "C1")],
                default="B1",
                max_length=2,
            ),
        ),
        migrations.AddField(
            model_name="userprogress",
            name="correct_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprogress",
            name="error_count",
            field=models.PositiveIntegerField(default=0),
        ),
        # New VocabularyWord model
        migrations.CreateModel(
            name="VocabularyWord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("word", models.CharField(max_length=128)),
                ("translation", models.CharField(blank=True, max_length=256)),
                ("transcription", models.CharField(blank=True, max_length=128)),
                ("definition", models.TextField(blank=True)),
                ("example", models.TextField(blank=True)),
                (
                    "level",
                    models.CharField(
                        choices=[("B1", "B1"), ("B2", "B2"), ("C1", "C1")],
                        default="B1",
                        max_length=2,
                    ),
                ),
                (
                    "novel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vocabulary",
                        to="novels.novel",
                    ),
                ),
            ],
            options={"ordering": ("word",)},
        ),
        # New Achievement model
        migrations.CreateModel(
            name="Achievement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=64, unique=True)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("icon", models.CharField(blank=True, max_length=64)),
                ("points", models.PositiveSmallIntegerField(default=10)),
            ],
        ),
        # New Quiz model
        migrations.CreateModel(
            name="Quiz",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("chapter_node_id", models.CharField(max_length=128)),
                ("title", models.CharField(blank=True, max_length=255)),
                ("pass_threshold", models.FloatField(default=0.6)),
                (
                    "novel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quizzes",
                        to="novels.novel",
                    ),
                ),
            ],
        ),
        # New QuizQuestion model
        migrations.CreateModel(
            name="QuizQuestion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.TextField()),
                (
                    "question_type",
                    models.CharField(
                        choices=[
                            ("single", "Single choice"),
                            ("multiple", "Multiple choice"),
                            ("fill", "Fill in the blank"),
                        ],
                        default="single",
                        max_length=16,
                    ),
                ),
                ("hint", models.TextField(blank=True)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                (
                    "quiz",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="questions",
                        to="novels.quiz",
                    ),
                ),
            ],
            options={"ordering": ("order",)},
        ),
        # New QuizChoice model
        migrations.CreateModel(
            name="QuizChoice",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.TextField()),
                ("is_correct", models.BooleanField(default=False)),
                ("explanation", models.TextField(blank=True)),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="choices",
                        to="novels.quizquestion",
                    ),
                ),
            ],
        ),
        # New QuizAttempt model
        migrations.CreateModel(
            name="QuizAttempt",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("score", models.FloatField(default=0.0)),
                ("max_score", models.FloatField(default=0.0)),
                ("passed", models.BooleanField(default=False)),
                ("answers", models.JSONField(default=dict)),
                ("completed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "quiz",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attempts",
                        to="novels.quiz",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quiz_attempts",
                        to="novels.userprofile",
                    ),
                ),
            ],
        ),
        # New UserAchievement model
        migrations.CreateModel(
            name="UserAchievement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("earned_at", models.DateTimeField(auto_now_add=True)),
                (
                    "achievement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="earned_by",
                        to="novels.achievement",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="achievements",
                        to="novels.userprofile",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="userachievement",
            unique_together={("user", "achievement")},
        ),
        # New UserVocabulary model
        migrations.CreateModel(
            name="UserVocabulary",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("learned_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="learned_words",
                        to="novels.userprofile",
                    ),
                ),
                (
                    "word",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="learned_by",
                        to="novels.vocabularyword",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="uservocabulary",
            unique_together={("user", "word")},
        ),
    ]
