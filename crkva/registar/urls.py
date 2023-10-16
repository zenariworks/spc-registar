from django.urls import path

from . import views
from .views import SvestenikView, SvestenikPDF
from .views import KrstenjeView, KrstenjePDF


urlpatterns = [
    path('', views.index, name='index'),
    path('svestenik/<int:sv_rbr>/', SvestenikView.as_view(), name='svestenik_detail'),
    path('svestenik/print/<int:pk>/', SvestenikPDF.as_view(), name='svestenik_pdf'),
    path('krstenje/<int:k_rbr>/', KrstenjeView.as_view(), name='krstenje_detail'),
    path('krstenje/print/<int:pk>/', KrstenjePDF.as_view(), name='krstenje_pdf'),
]
