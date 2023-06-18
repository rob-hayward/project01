from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.signals import user_logged_in
from enum import Enum
from decimal import Decimal
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField
from django.db.models import Avg, Count, StdDev


USER_INACTIVE_PERIOD = 1000  # number of days


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


class AnswerType(Enum):
    BINARY = 'BINARY'
    SCALE_DECIMAL = 'SCALE_DECIMAL'
    SCALE_INT = 'SCALE_INT'
    # Add other types as needed.


class Status(Enum):
    PROPOSED = 'proposed'
    APPROVED = 'approved'
    LIVE = 'live'
    REJECTED = 'rejected'


class Tag(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class KeywordDefinition(models.Model):
    keyword = models.CharField(max_length=255, unique=True)
    definition = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[(status.name, status.value) for status in Status],
        default=Status.PROPOSED.value
    )

    def __str__(self):
        return self.keyword


class Question(models.Model):
    status = models.CharField(
        max_length=20,
        choices=[(status.name, status.value) for status in Status],
        default=Status.PROPOSED.value
    )
    answer_type = models.CharField(
        max_length=30,
        choices=[(answer_type.name, answer_type.value) for answer_type in AnswerType],
        default=AnswerType.BINARY.name,
    )
    parent_question = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True,
                                        related_name='child_questions')
    question_text = models.TextField()
    main_tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='main_questions', null=True, blank=True)
    additional_tags = models.ManyToManyField(Tag, blank=True, related_name='additional_questions')
    keywords = models.ManyToManyField(KeywordDefinition, related_name='questions')
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    approval_threshold = models.IntegerField(default=100)  # Approval threshold
    rejection_threshold = models.IntegerField(default=100)  # Rejection threshold
    participation_threshold = models.IntegerField(default=100)  # Participation threshold

    def check_question_status(self):  # New method
        vote_data = ProposalVoteData.objects.get(question=self)
        if vote_data.participation_percentage >= self.participation_threshold:
            if vote_data.approval_percentage >= self.approval_threshold:
                self.status = Status.APPROVED.value
            elif vote_data.rejection_percentage >= self.rejection_threshold:
                self.status = Status.REJECTED.value
        self.save()

    def get_additional_tags(self):
        return self.additional_tags.all()

    def __str__(self):
        return self.question_text

    def question_path(self):
        path = []
        question = self
        while question is not None:
            path.append(question.main_tag)
            question = question.parent_question
        return path[::-1]  # reversed so that it starts from root


class ProposalVoteManager(models.Manager):
    def submit_vote(self, user, question, vote):
        if vote == VoteType.NO_VOTE.value:  # if vote is "no-vote"
            self.filter(user=user, question=question).delete()  # delete the existing vote if it exists
            ProposalVoteData.update_vote_data(question)
        else:
            proposal_vote, created = self.update_or_create(
                user=user,
                question=question,
                defaults={'vote': vote}  # sets vote value for new and existing objects
            )


class ProposalVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    vote = models.IntegerField(choices=VoteType.choices(), default=VoteType.default())
    objects = ProposalVoteManager()

    class Meta:
        unique_together = ['user', 'question']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ProposalVoteData.update_vote_data(self.question)
        self.question.check_question_status()


class ProposalVoteData(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, primary_key=True)
    total_votes = models.IntegerField(default=0)
    total_approve_votes = models.IntegerField(default=0)
    total_reject_votes = models.IntegerField(default=0)
    approval_percentage = models.FloatField(default=0)
    rejection_percentage = models.FloatField(default=0)
    participation_percentage = models.FloatField(default=0)

    @classmethod
    def update_vote_data(cls, question):
        total_votes = ProposalVote.objects.filter(question=question).count()
        total_approve_votes = ProposalVote.objects.filter(question=question, vote=VoteType.APPROVE.value).count()
        total_reject_votes = ProposalVote.objects.filter(question=question, vote=VoteType.REJECT.value).count()
        approval_percentage = (total_approve_votes / total_votes) * 100 if total_votes > 0 else 0
        rejection_percentage = (total_reject_votes / total_votes) * 100 if total_votes > 0 else 0
        total_users = UserProfile.objects.filter(is_live=True).count()
        participation_percentage = (total_votes / total_users) * 100 if total_users > 0 else 0

        vote_data, created = cls.objects.get_or_create(question=question)
        vote_data.total_votes = total_votes
        vote_data.total_approve_votes = total_approve_votes
        vote_data.total_reject_votes = total_reject_votes
        vote_data.approval_percentage = approval_percentage
        vote_data.rejection_percentage = rejection_percentage
        vote_data.participation_percentage = participation_percentage
        vote_data.save()


class AnswerBinary(models.Model):
    ANSWER_CHOICES = [
        (0, 'No answer'),
        (-1, 'No'),
        (1, 'Yes'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.IntegerField(choices=ANSWER_CHOICES)


class AnswerBinaryData(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, primary_key=True)
    total_positive = models.IntegerField(default=0)
    total_negative = models.IntegerField(default=0)
    positive_percentage = models.FloatField(default=0)
    negative_percentage = models.FloatField(default=0)


class AnswerInteger(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.IntegerField(null=True, blank=True)

    @classmethod
    def get_data(cls, question):
        answers = cls.objects.filter(question=question)

        # Calculate statistics using Django's aggregation functions
        return answers.aggregate(
            mean=Avg('answer'),
            count=Count('answer'),
            std_dev=StdDev('answer'),
        )


class AnswerDecimal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    @classmethod
    def get_data(cls, question):
        answers = cls.objects.filter(question=question)

        # Calculate statistics using Django's aggregation functions
        return answers.aggregate(
            mean=Avg('answer'),
            count=Count('answer'),
            std_dev=StdDev('answer'),
        )


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


# Signal to create or update user profile when user is created or updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, preferred_name='', address='', city='', post_code='', country='',
                                   phone_number='')
    else:
        instance.userprofile.save()
