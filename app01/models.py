from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.signals import user_logged_in
from enum import Enum
from django.core.exceptions import ValidationError

USER_INACTIVE_PERIOD = 1000  # number of days


class InputType(Enum):
    YES_NO = 'Yes / No'
    SCALE_FLOAT = 'Scale (floating point)'
    SCALE_INT = 'Scale (integer)'
    #     add other input types as needed


class QuestionStatus(Enum):
    PROPOSED = 'proposed'
    APPROVED = 'approved'
    ACTIVE = 'active'
    REJECTED = 'rejected'


class Tag(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class KeywordDefinition(models.Model):
    keyword = models.CharField(max_length=255, unique=True)
    definition = models.TextField()

    def __str__(self):
        return self.keyword


class ProposedKeywordDefinition(models.Model):
    keyword = models.ForeignKey(KeywordDefinition, on_delete=models.CASCADE)
    new_definition = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    # other fields for handling the voting/approval process...


class Question(models.Model):
    status = models.CharField(
        max_length=20,
        choices=[(status, status.value) for status in QuestionStatus],
        default=QuestionStatus.PROPOSED.value
    )
    parent_question = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True,
                                        related_name='child_questions')
    question_text = models.TextField()
    input_type = models.CharField(max_length=30, choices=[(type.name, type.value) for type in InputType])
    main_tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='main_questions', null=True, blank=True) # main tag
    additional_tags = models.ManyToManyField(Tag, blank=True, related_name='additional_questions') # additional tags
    keywords = models.ManyToManyField(KeywordDefinition, related_name='questions')
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.question_text

    def question_path(self):
        path = []
        question = self
        while question is not None:
            path.append(question.main_tag)
            question = question.parent_question
        return path[::-1]  # reversed so that it starts from root


class UserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(null=True)
    answer_integer = models.IntegerField(null=True)
    answer_float = models.FloatField(null=True)

    def set_answer(self, answer):
        if self.question.input_type == InputType.YES_NO.value:
            self.answer_text = answer
        elif self.question.input_type == InputType.SCALE_FLOAT.value:
            try:
                self.answer_float = float(answer)
            except ValueError:
                raise ValidationError("The answer provided cannot be converted to a float.")
        elif self.question.input_type == InputType.SCALE_INT.value:
            try:
                self.answer_integer = int(answer)
            except ValueError:
                raise ValidationError("The answer provided cannot be converted to an integer.")
        # add conditions for other possible input types here

    def __str__(self):
        return f'{self.user.username} - {self.question.question_text}'


class BinaryVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    vote = models.BooleanField(null=True)

    class Meta:
        unique_together = ['user', 'question']


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    preferred_name = models.CharField(max_length=255, blank=True)  # New field
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    post_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=True)  # change default to False once verification is implemented
    is_live = models.BooleanField(default=True)
    last_visited = models.DateTimeField(default=timezone.now)

    def check_user_status(self):
        # Set `is_live` to False if user hasn't visited the site for USER_INACTIVE_PERIOD number of days
        if self.last_visited < timezone.now() - timedelta(days=USER_INACTIVE_PERIOD):
            self.is_live = False
        else:
            self.is_live = True
        self.save()

    def __str__(self):
        return self.user.username


@receiver(user_logged_in, sender=User)
def update_last_visit(sender, user, request, **kwargs):
    profile = UserProfile.objects.get(user=user)
    profile.last_visited = timezone.now()
    profile.check_user_status()  # calling check_user_status when user logs in
    profile.save()


user_logged_in.connect(update_last_visit)


# Signal to create or update user profile when user is created or updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, preferred_name='', address='', city='', post_code='', country='', phone_number='')
    else:
        instance.userprofile.save()
