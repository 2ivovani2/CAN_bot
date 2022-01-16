from django import template

register = template.Library()

@register.filter(name='times') 
def times(number):
    return range(number)

@register.filter(name='get_by_index')
def get_by_index(indexable, i):
    return indexable[i]