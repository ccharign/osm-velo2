# -*- coding:utf-8 -*-
from django import forms
import dijk.models as mo


class FormCycla(forms.Form):
    """
    Pour demander la zone de laquelle afficher la carte de cycla.
    """
    zone = forms.ModelChoiceField(queryset=mo.Zone.objects.all(), label='Zone')
    force_calcul = forms.BooleanField(label="Forcer le calcul", required=False)


class ChoixZone(forms.Form):
    """
    Choix de zone. A priori pour la page d'index.
    """
    zone = forms.ModelChoiceField(queryset=mo.Zone.objects.all(), label="")


class RechercheBase(forms.Form):
    """
    Classe mère pour les formulaires de recherche d’itinéraire
    """
    départ = forms.CharField(label="Départ", required=False)
    coords_départ = forms.CharField(widget=forms.HiddenInput(), required=False)
    partir_de_ma_position = forms.BooleanField(label="Partir de ma position", required=False, initial=False)
    arrivée = forms.CharField(label="Arrivée")
    coords_arrivée = forms.CharField(widget=forms.HiddenInput(), required=False)
    #zone_t = forms.CharField(widget=forms.HiddenInput())
    zone = forms.ModelChoiceField(queryset=mo.Zone.objects.all(), widget=forms.HiddenInput())
    marqueurs_é = forms.CharField(widget=forms.HiddenInput(), required=False)  # Pour les marqueurs d’étapes précédents.
    marqueurs_i = forms.CharField(widget=forms.HiddenInput(), required=False)  # Pour les marqueurs d’étape interdite précédents.
    


class Recherche(RechercheBase):
    """
    Recherche initiale.
    """
    #partir_de_ma_position = forms.BooleanField(label="Partir de ma position", required=False, initial=False)
    # pourcentage_détour = forms.CharField(widget=forms.HiddenInput())


class RelanceRapide(RechercheBase):
    """
    Pour relancer rapidement une recherche.
    """
    départ = forms.CharField(widget=forms.HiddenInput())
    arrivée = forms.CharField(widget=forms.HiddenInput())
    étapes = forms.CharField(widget=forms.HiddenInput(), required=False)
    rues_interdites = forms.CharField(widget=forms.HiddenInput(), required=False)
    pourcentage_détour = forms.CharField(widget=forms.HiddenInput())
    partir_de_ma_position = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)


class ToutCaché(RechercheBase):
    """
    Pour ce formulaire, tout est caché. Utilisé pour « trajet retour ».
    """
    départ = forms.CharField(widget=forms.HiddenInput())
    arrivée = forms.CharField(widget=forms.HiddenInput())
    pourcentage_détour = forms.CharField(widget=forms.HiddenInput())
    étapes = forms.CharField(widget=forms.HiddenInput(), required=False)
    rues_interdites = forms.CharField(widget=forms.HiddenInput(), required=False)
    partir_de_ma_position = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)


class EnregistrerContrib(ToutCaché):
    """
    Pour enregistrer une contribution.
    """
    # départ = forms.CharField(widget=forms.HiddenInput())
    # coords_départ = forms.CharField(widget=forms.HiddenInput())
    # arrivée = forms.CharField(widget=forms.HiddenInput())
    # coords_arrivée = forms.CharField(widget=forms.HiddenInput())
    # zone_t = forms.CharField(widget=forms.HiddenInput())
    # étapes = forms.CharField(widget=forms.HiddenInput())
    # rues_interdites = forms.CharField(widget=forms.HiddenInput())
    AR = forms.BooleanField(label="Valable aussi pour le retour ?", required=False)


# Nom osm des lieux proposés dans le formulaire.
TYPE_AMEN_POUR_AUTOUR_DE_MOI = [
    "pharmacy", "post_office", "doctors", "bank", "fast_food",
    "restaurant", "cafe", "marketplace", "police", "bar", "pub",
    "drinking_water", "atm", "water_point", "convenience",
    "bakery", "greengrocer", "supermarket", "toilets", "hospital",
    "bicycle_rental", "fountain", "hardware", "clothes", "sports",
    "laundry", "variety_store", "chemist", "pastry", "outdoor",
    "mall", "bureau_de_change",
]


class AutourDeMoi(forms.Form):
    """
    Pour afficher la carte autour de l’utilisateur, et rechercher des amenities.
    Le champ localisation sera rempli par le javascript.
    """
    type_lieu = forms.ModelMultipleChoiceField(
        queryset=mo.TypeLieu.objects.filter(nom_osm__in=TYPE_AMEN_POUR_AUTOUR_DE_MOI),
        label="Type de lieu",
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    rayon = forms.FloatField(label="Chercher dans un rayon de (en km) :", initial=.4)
    localisation = forms.CharField(widget=forms.HiddenInput, initial="-0.36667,43.299999")


class RapportDeBug(forms.ModelForm):  # créer un form automatiquement depuis un modèle https://docs.djangoproject.com/en/4.0/topics/forms/modelforms/
    """
    Pour rentrer un rapport de bug.
    Construit automatiquent à partir du modèle éponyme.
    """
    class Meta:
        model = mo.Bug
        fields = ["importance", "titre", "description", "message_d_erreur", "comment_reproduire", "contact"]
