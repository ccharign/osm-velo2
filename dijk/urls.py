from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from . import views

urlpatterns = [
    path("resultat", views.recherche, name="résultat"),
    path("relance_rapide", views.relance_rapide, name="relance_rapide"),
    path("retour", views.trajet_retour, name="retour"),
    
    path("contribution", views.contribution, name="contribution"),
    path("mode_demploi", views.mode_demploi, name="mode d’emploi"),
    path("limitations", views.limitations, name="limitations"),
    path("sous_le_capot", views.sous_le_capot, name="sous le capot"),
    path("rapport_de_bug", views.rapport_de_bug, name="bug"),
    path("autourDeMoi", views.autourDeMoi, name="Autour de moi"),
    
    #path("visu_nv_chemin", views.visualisation_nv_chemin, name="visu nv chemin"),
    path("confirme_nv_chemin", views.confirme_nv_chemin, name="confirme nv chemin"),

    path("pourcentages/", views.recherche_pourcentages, name="recherche pourcentages"),
    path("pourcentages_res/<str:ville>", views.vue_pourcentages_piétons_pistes_cyclables, name="stats"),
    path("pourcentages_res/", views.vue_pourcentages_piétons_pistes_cyclables, name="stats"),
    
    path("cycla/<str:zone_t>", views.carte_cycla, name="carte cycla"),
    path("cycla/", views.choix_cycla, name="cycla"),

    path("telechargement/", views.téléchargement, name="téléchargement"),

    path("chemins/", views.affiche_chemins, name="affiche chemins"),
    path("modif_chemin/", views.action_chemin, name="modif chemin"),

    path("fouine/", views.fouine, name="fouine"),
    
    path('ajax/recherche_rue/', views.pour_complétion, name="complète rue"),
    path('', views.choix_zone, name='index'),
    path('recherche/<str:zone_t>/', views.recherche, name='recherche'),




] + staticfiles_urlpatterns()

