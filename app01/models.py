from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.signals import user_logged_in
from enum import Enum
from decimal import Decimal
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField
from django.db.models import Avg, Count, StdDev
from django.contrib.contenttypes.models import ContentType


USER_INACTIVE_PERIOD = 365  # number of days
APPROVE_THRESHOLD = 50
REJECT_THRESHOLD = 50


class VoteType(Enum):
    APPROVE = 1
    REJECT = -1
    NO_VOTE = 0

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]

    @classmethod
    def default(cls):
        return cls.NO_VOTE.value


class Status(Enum):
    PROPOSED = 'Proposed'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'
    ALTERNATIVE = 'Alternative'


class AnswerType(Enum):
    BINARY = 'BINARY'
    SCALE_DECIMAL = 'SCALE_DECIMAL'
    SCALE_INT = 'SCALE_INT'
    # Add other types as needed.


class Votable(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[(status.name, status.value) for status in Status],
        default=Status.PROPOSED.value
    )
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    participation_percentage = models.DecimalField(max_digits=3, decimal_places=0, default=0)
    approval_percentage = models.DecimalField(max_digits=3, decimal_places=0, default=0)
    total_votes = models.PositiveIntegerField(default=0)
    total_approve_votes = models.PositiveIntegerField(default=0)
    total_reject_votes = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True  # This makes Votable an abstract base class

    def get_vote_data(self):
        content_type = ContentType.objects.get_for_model(self.__class__)

        total_votes = Vote.objects.filter(
            votable_content_type=content_type,
            votable_object_id=self.id
        ).exclude(vote=VoteType.NO_VOTE.value).count()

        vote_data = Vote.objects.filter(
            votable_content_type=content_type,
            votable_object_id=self.id
        ).exclude(vote=VoteType.NO_VOTE.value).aggregate(
            total_approve_votes=Count('id', filter=models.Q(vote=VoteType.APPROVE.value)),
            total_reject_votes=Count('id', filter=models.Q(vote=VoteType.REJECT.value)),
        )

        total_approve_votes = vote_data['total_approve_votes']
        total_reject_votes = vote_data['total_reject_votes']

        total_users = UserProfile.objects.filter(is_live=True).count()
        self.participation_percentage = (total_votes / total_users) * 100 if total_users > 0 else 0
        self.approval_percentage = (total_approve_votes / total_votes) * 100 if total_votes > 0 else 0
        rejection_percentage = (total_reject_votes / total_votes) * 100 if total_votes > 0 else 0

        self.total_votes = total_votes
        self.total_approve_votes = total_approve_votes
        self.total_reject_votes = total_reject_votes

        # Change the status if the thresholds are met
        if self.approval_percentage > APPROVE_THRESHOLD:
            self.status = Status.APPROVED.value
        elif rejection_percentage > REJECT_THRESHOLD:
            self.status = Status.REJECTED.value
        else:
            self.status = Status.PROPOSED.value

        self.save()

        vote_data = {
            'status': self.status,
            'total_votes': total_votes,
            'approval_percentage': self.approval_percentage,
            'rejection_percentage': 100 - self.approval_percentage,
            'participation_percentage': self.participation_percentage,
            'total_approve_votes': total_approve_votes,
            'total_reject_votes': total_reject_votes,
        }

        return vote_data

    def get_votes(self):
        content_type = ContentType.objects.get_for_model(self)
        return Vote.objects.filter(votable_content_type=content_type, votable_object_id=self.id)

    def get_user_vote(self, user):
        content_type = ContentType.objects.get_for_model(self)
        try:
            vote = Vote.objects.get(votable_content_type=content_type, votable_object_id=self.id, user=user)
            if vote.vote == 1:
                user_vote = 'Approve'
            elif vote.vote == -1:
                user_vote = 'Reject'
            else:
                user_vote = 'No Vote'
            return user_vote
        except Vote.DoesNotExist:
            return 'No Vote'

    def get_alternatives(self):
        return self.children.filter(status=Status.ALTERNATIVE.value)


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    votable_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    votable_object_id = models.PositiveIntegerField()
    votable = GenericForeignKey('votable_content_type', 'votable_object_id')
    vote = models.IntegerField(choices=VoteType.choices(), default=VoteType.default())
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'votable_content_type', 'votable_object_id']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.votable.get_vote_data()


class KeyWord(Votable):
    word = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.word

    def get_absolute_url(self):
        return reverse('app01:keyword_detail', args=[str(self.word)])


class KeyWordDefinition(Votable):
    keyword = models.OneToOneField(KeyWord, on_delete=models.CASCADE, related_name='definition')
    definition = models.TextField()
    questions = models.ManyToManyField('Question', related_name='keyword_definitions')

    def __str__(self):
        return self.definition


class QuestionTag(Votable):
    keywords = models.ManyToManyField(KeyWord)

    def __str__(self):
        return f'{", ".join([keyword.word for keyword in self.keywords.all()])}'


class Question(Votable):
    question_tag = models.OneToOneField(QuestionTag, on_delete=models.CASCADE, related_name="question")
    question_text = models.TextField()
    answer_type = models.CharField(
        max_length=30,
        choices=[(answer_type.name, answer_type.value) for answer_type in AnswerType],
        default=AnswerType.BINARY.name,
    )

    def __str__(self):
        return self.question_text

    def question_path(self):
        path = []
        question = self
        while question is not None:
            path.append(question.question_tag)
            question = question.parent
        return path[::-1]  # reversed so that it starts from root


class AnswerBinary(Votable):
    question_tag = models.OneToOneField(QuestionTag, on_delete=models.CASCADE, related_name="question_tag")


# class AnswerInteger(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     question = models.ForeignKey(Question, on_delete=models.CASCADE)
#     answer = models.IntegerField(null=True, blank=True)
#
#     @classmethod
#     def get_data(cls, question):
#         answers = cls.objects.filter(question=question)
#
#         # Calculate statistics using Django's aggregation functions
#         return answers.aggregate(
#             mean=Avg('answer'),
#             count=Count('answer'),
#             std_dev=StdDev('answer'),
#         )
#
#
# class AnswerDecimal(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     question = models.ForeignKey(Question, on_delete=models.CASCADE)
#     answer = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
#
#     @classmethod
#     def get_data(cls, question):
#         answers = cls.objects.filter(question=question)
#
#         # Calculate statistics using Django's aggregation functions
#         return answers.aggregate(
#             mean=Avg('answer'),
#             count=Count('answer'),
#             std_dev=StdDev('answer'),
#         )
#
#
# class DesignBrief:
#     pass
#
#
# class Design:
#     pass


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    preferred_name = models.CharField(max_length=255, blank=True)  # New field
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    post_code = models.CharField(max_length=20, blank=True)
    country = CountryField(blank_label='(select country)')
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


# Signal to update user profile when user is updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if not created:
        instance.userprofile.save()

