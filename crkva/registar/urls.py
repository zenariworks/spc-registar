from django.urls import path

from . import views
from .views import SvestenikView, SvestenikPDF


urlpatterns = [
    path('', views.index, name='index'),
    path('svestenik/<int:sv_rbr>/', SvestenikView.as_view(), name='svestenik_detail'),
    path('svestenik/print/<int:pk>/', SvestenikPDF.as_view(), name='svestenik_pdf'),
]
