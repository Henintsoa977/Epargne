import numpy as np

def methode_euler_epargne(epargne_initiale, depot_mensuel, taux_annuel, duree_mois, pas=1):

    #Résolution numérique avec Euler
    
    r = taux_annuel / 12 / 100   
    epargne = epargne_initiale
    resultats = []
    
    for mois in range(1, duree_mois + 1):
        # Calcul de l'intérêt du mois
        interet = epargne * r
        
        epargne = epargne + interet + depot_mensuel
        
        resultats.append({
            'mois': mois,
            'epargne': round(epargne, 2),
            'interet': round(interet, 2),
            'depot': depot_mensuel
        })
    
    return resultats