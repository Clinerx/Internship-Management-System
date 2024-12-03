from django import template
import mimetypes


register = template.Library()

@register.filter
def is_pdf(file_url):
    return file_url.lower().endswith('.pdf')

@register.filter
def is_pdf(url):
    mime_type, _ = mimetypes.guess_type(url)
    return mime_type == 'application/pdf'