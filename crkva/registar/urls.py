from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('svestenik/<int:sv_rbr>/', views.svestenik_detail, name='svestenik_detail'),
    path('svestenik/print/<int:pk>/', views.SvestenikPDFView.as_view(), name='svestenik_pdf'),
]
