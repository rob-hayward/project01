import re
from django import template
from django.utils.safestring import mark_safe
from app01.models import Keyword
import nltk
from nltk.tokenize import word_tokenize

nltk.download('punkt', quiet=True)

register = template.Library()


@register.filter(is_safe=True)
def highlight_keywords(text):
    words = re.findall(r"[\w']+|[.,!?;]", text)
    for i, word in enumerate(words):
        # Remove leading/trailing punctuation
        clean_word = re.sub(r"^\W+|\W+$", "", word)
        if clean_word.isalnum():
            try:
                keyword = Keyword.objects.get(word__iexact=clean_word)
                if keyword.status == 'Approved':
                    words[i] = word.replace(clean_word, f'<a href="{keyword.get_absolute_url()}" class="keyword approved" data-word="{clean_word}">{keyword.word}</a>')
                elif keyword.status == 'Proposed':
                    words[i] = word.replace(clean_word, f'<a href="{keyword.get_absolute_url()}" class="keyword proposed" data-word="{clean_word}">{keyword.word}</a>')
                elif keyword.status == 'Rejected':
                    words[i] = word.replace(clean_word, f'<a href="{keyword.get_absolute_url()}" class="keyword rejected" data-word="{clean_word}">{keyword.word}</a>')
            except Keyword.DoesNotExist:
                words[i] = f'<span data-word="{clean_word}">{clean_word}</span>'
    result = ' '.join(words)
    # post-processing to remove unwanted spaces
    result = result.replace(" ,", ",").replace(" .", ".").replace(" !", "!").replace(" ?", "?").replace(" ;", ";")
    return mark_safe(result)
