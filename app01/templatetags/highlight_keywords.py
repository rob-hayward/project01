from django import template
from django.utils.safestring import mark_safe
from app01.models import KeyWord
import nltk
from nltk.tokenize import word_tokenize

nltk.download('punkt', quiet=True)  # This line will download the 'punkt' package if it isn't already downloaded

register = template.Library()


@register.filter(is_safe=True)
def highlight_keywords(text):
    words = word_tokenize(text)
    for i, word in enumerate(words):
        # Only processing words which are not punctuation
        if word.isalnum():
            try:
                keyword = KeyWord.objects.get(name=word)
                if keyword.status == 'approved':
                    words[i] = f'<a href="{keyword.get_absolute_url()}" class="keyword approved">{word}</a>'
                elif keyword.status == 'proposed':
                    words[i] = f'<a href="{keyword.get_absolute_url()}" class="keyword proposed">{word}</a>'
                elif keyword.status == 'rejected':
                    words[i] = f'<a href="{keyword.get_absolute_url()}" class="keyword rejected">{word}</a>'
            except KeyWord.DoesNotExist:
                pass
    return mark_safe(' '.join(words))
