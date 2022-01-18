from django.template.loader import render_to_string
from django.utils.html import strip_tags
import pdfkit

def generate_report(data:dict={}, image_link:str=None, product_name:str=None):
    """
        Функция генерации отчета пользователю
    """

    html_message = render_to_string('report.html', {
        'product_name': product_name,
        'image_link': image_link,
        'positive':data['good_points'].items(),
        'negative':data['bad_points'].items(),

    })
    

    pdf = pdfkit.from_string(html_message, False, options={
        'encoding': "UTF-8",
    }) 
    
    return pdf
