# -*- coding:utf-8 -*-
from django import forms
import dijk.models as mo


class CarteCycla(forms.Form):
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
    Classe mère pour les formulaires de recherche d’itinéraire.
    """
    départ = forms.CharField(label="Départ", required=False)
    données_cachées_départ = forms.CharField(widget=forms.HiddenInput(), required=False)  # Sera rempli par l’autocomplétion
    partir_de_ma_position = forms.BooleanField(label="Partir de ma position", required=False, initial=False)
    localisation = forms.CharField(widget=forms.HiddenInput(), required=False)
    arrivée = forms.CharField(label="Arrivée")
    données_cachées_arrivée = forms.CharField(widget=forms.HiddenInput(), required=False)
    zone = forms.ModelChoiceField(queryset=mo.Zone.objects.all(), widget=forms.HiddenInput())
    # marqueurs_é = forms.CharField(widget=forms.HiddenInput(), required=False)  # Pour les marqueurs d’étapes précédents.
    # marqueurs_i = forms.CharField(widget=forms.HiddenInput(), required=False)  # Pour les marqueurs d’étape interdite précédents.
    étapes = forms.CharField(widget=forms.HiddenInput(), required=False)
    rues_interdites = forms.CharField(widget=forms.HiddenInput(), required=False)
    passer_par = forms.ModelChoiceField(queryset=mo.GroupeTypeLieu.objects.all(), required=False, widget=forms.HiddenInput())
    étapes_inter = forms.CharField(widget=forms.HiddenInput(), required=False)
    toutes_les_étapes = forms.CharField(widget=forms.HiddenInput(), required=False)


class Recherche(RechercheBase):
    """
    Recherche initiale.
    """
    passer_par = forms.ModelChoiceField(queryset=mo.GroupeTypeLieu.objects.all(), label="(facultatif) Passer par un(e) : ", required=False)
    # partir_de_ma_position = forms.BooleanField(label="Partir de ma position", required=False, initial=False)
    # pourcentage_détour = forms.CharField(widget=forms.HiddenInput())


class RelanceRapide(RechercheBase):
    """
    Pour relancer rapidement une recherche.
    """
    # départ = forms.CharField(widget=forms.HiddenInput(), required=False)
    arrivée = forms.CharField(label="Arrivée", required=False)
    pourcentage_détour = forms.CharField(widget=forms.HiddenInput())
    partir_de_ma_position = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)


class ToutCaché(RechercheBase):
    """
    Pour ce formulaire, tout est caché. Utilisé pour « trajet retour ».
    """
    départ = forms.CharField(widget=forms.HiddenInput(), required=False)
    arrivée = forms.CharField(widget=forms.HiddenInput(), required=False)
    pourcentage_détour = forms.CharField(widget=forms.HiddenInput())
    partir_de_ma_position = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)


class EnregistrerContrib(ToutCaché):
    """
    Pour enregistrer une contribution.
    """
    autre_p_détour = forms.IntegerField(label="Optionnel : autre profil cycliste", help_text="N’importe quel nombre strictement positif sachant que  pour « priorité confort, cette valeur est à 30 et pour « intermédiaire » elle est à 15.", required=False, min_value=1, widget=forms.HiddenInput())
    AR = forms.BooleanField(label="Valable aussi pour le retour ?", required=False)

    
# Nom osm des lieux proposés dans le formulaire.
# TYPE_AMEN_POUR_AUTOUR_DE_MOI = [
#     "pharmacy", "post_office", "doctors", "bank", "fast_food",
#     "restaurant", "cafe", "marketplace", "police", "bar", "pub",
#     "drinking_water", "atm", "water_point", "convenience",
#     "bakery", "greengrocer", "supermarket", "toilets", "hospital",
#     "bicycle_rental", "fountain", "hardware", "clothes", "sports",
#     "laundry", "variety_store", "chemist", "pastry", "outdoor",
#     "mall", "bureau_de_change",
# ]


class AutourDeMoi(forms.Form):
    """
    Pour afficher la carte autour de l’utilisateur, et rechercher des amenities.
    Le champ localisation sera rempli par le javascript.
    """
    gtls = forms.ModelMultipleChoiceField(
        queryset=mo.GroupeTypeLieu.objects.all(),
        label="Chercher un type de lieu :",
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    localisation = forms.CharField(widget=forms.HiddenInput, initial="-0.36667,43.299999")
    bbox = forms.CharField(widget=forms.HiddenInput())


class RapportDeBug(forms.ModelForm):  # créer un form automatiquement depuis un modèle https://docs.djangoproject.com/en/4.0/topics/forms/modelforms/
    """
    Pour rentrer un rapport de bug.
    Construit automatiquent à partir du modèle éponyme.
    """
    class Meta:
        model = mo.Bug
        fields = ["importance", "titre", "description", "message_d_erreur", "comment_reproduire", "contact"]
