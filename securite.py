"""
Sécurité des mots de passe : hachage PBKDF2-SHA256 avec sel aléatoire.

N'utilise que la bibliothèque standard (aucune dépendance à installer).
Format stocké :  pbkdf2_sha256$<itérations>$<sel base64>$<hash base64>

Compatibilité : un mot de passe ancien (texte clair) est encore reconnu à la
connexion, puis converti automatiquement en haché (cf. doit_etre_rehache).
"""

import base64
import hashlib
import hmac
import os
import re
import threading
import time
import unicodedata

ALGO = "pbkdf2_sha256"
ITERATIONS = 600_000          # recommandation OWASP 2023 pour PBKDF2-SHA256
LONGUEUR_MINI = 12


def _b64(octets):
    return base64.b64encode(octets).decode("ascii")


def hasher_mot_de_passe(mot_de_passe, iterations=ITERATIONS):
    """Retourne le haché (avec sel et nombre d'itérations) d'un mot de passe."""
    sel = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", str(mot_de_passe).encode("utf-8"), sel, iterations)
    return f"{ALGO}${iterations}${_b64(sel)}${_b64(dk)}"


def est_hache(valeur):
    """True si la valeur stockée est déjà au format haché."""
    return (
        isinstance(valeur, str)
        and valeur.startswith(ALGO + "$")
        and valeur.count("$") == 3
    )


def verifier_mot_de_passe(mot_de_passe, stocke):
    """Compare un mot de passe saisi à la valeur stockée (hachée, ou ancien
    format texte clair). Comparaison à temps constant."""
    if mot_de_passe is None or not isinstance(stocke, str) or stocke == "":
        return False
    if est_hache(stocke):
        try:
            _, iterations, sel_b64, hash_b64 = stocke.split("$")
            attendu = base64.b64decode(hash_b64)
            calcule = hashlib.pbkdf2_hmac(
                "sha256", str(mot_de_passe).encode("utf-8"),
                base64.b64decode(sel_b64), int(iterations),
            )
            return hmac.compare_digest(calcule, attendu)
        except Exception:
            return False
    # Ancien format : texte clair (à convertir dès que possible)
    return hmac.compare_digest(str(mot_de_passe).encode("utf-8"), stocke.encode("utf-8"))


def doit_etre_rehache(stocke):
    """True si la valeur stockée est en clair ou utilise moins d'itérations
    que le réglage actuel."""
    if not est_hache(stocke):
        return True
    try:
        return int(stocke.split("$")[1]) < ITERATIONS
    except Exception:
        return True


# Mots (une fois chiffres/symboles retirés) trop courants ou trop liés au contexte.
_MOTS_FAIBLES = {
    "password", "passw0rd", "motdepasse", "mdp", "azerty", "azertyuiop", "qwerty",
    "qwertyuiop", "admin", "administrateur", "administrator", "root", "user",
    "lpee", "beton", "laboratoire", "labo", "chantier", "lgv", "casablanca",
    "maroc", "morocco", "welcome", "bienvenue", "bonjour", "changeme",
    "changezmoi", "letmein", "iloveyou", "soleil", "azertyazerty",
}


def _lettres_seules(texte):
    """Minuscules, sans accents, sans chiffres ni symboles."""
    nfkd = unicodedata.normalize("NFKD", str(texte))
    sans_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", sans_accents.lower())


def valider_mot_de_passe(mot_de_passe, username=""):
    """Règles pour un NOUVEAU mot de passe. Retourne un message d'erreur, ou
    None si le mot de passe est accepté.

    Les comptes existants ne sont pas touchés : la règle ne s'applique qu'à la
    création ou au changement d'un mot de passe."""
    mdp = mot_de_passe or ""
    if len(mdp) < LONGUEUR_MINI:
        return f"Le mot de passe doit contenir au moins {LONGUEUR_MINI} caractères."
    bas = mdp.strip().lower()
    nom = str(username or "").strip().lower()
    if nom and len(nom) >= 3 and nom in bas:
        return "Le mot de passe ne doit pas contenir le nom d'utilisateur."
    if mdp.isdigit():
        return "Le mot de passe ne peut pas être composé uniquement de chiffres."
    if len(set(mdp)) <= 4:
        return "Le mot de passe est trop répétitif : utilisez des caractères variés."
    lettres = _lettres_seules(mdp)
    if bas in _MOTS_FAIBLES or lettres in _MOTS_FAIBLES:
        return "Ce mot de passe est trop courant. Choisissez une phrase de passe plus originale."
    # Mot faible répété ou suivi d'un simple suffixe (ex. « lpeelpeelpee2026 »)
    for faible in _MOTS_FAIBLES:
        if len(faible) >= 4 and lettres and lettres == faible * (len(lettres) // len(faible)):
            return "Ce mot de passe est trop courant. Choisissez une phrase de passe plus originale."
    return None


class RegistreEchecs:
    """Compteur d'échecs de connexion par identifiant, en mémoire et
    thread-safe. À créer UNE SEULE FOIS par processus (st.cache_resource) :
    il est alors partagé par toutes les sessions, donc rafraîchir la page ou
    ouvrir un autre onglet ne remet pas le compteur à zéro.

    Après `seuil` échecs rapprochés, l'identifiant est bloqué `duree_blocage`
    secondes. Le compteur repart de zéro si le dernier échec date de plus de
    `fenetre` secondes. Le registre est vidé au redémarrage de l'application.
    """

    def __init__(self, seuil=5, duree_blocage=900, fenetre=900, max_entrees=5000):
        self.seuil = seuil
        self.duree_blocage = duree_blocage
        self.fenetre = fenetre
        self.max_entrees = max_entrees
        self._verrou = threading.Lock()
        self._donnees = {}

    @staticmethod
    def _cle(identifiant):
        return str(identifiant or "").strip().upper() or "_VIDE_"

    def secondes_restantes(self, identifiant, maintenant=None):
        """Secondes de blocage restantes (0 si l'identifiant n'est pas bloqué)."""
        t = time.time() if maintenant is None else maintenant
        with self._verrou:
            e = self._donnees.get(self._cle(identifiant))
            if not e:
                return 0
            return max(0, int(e["bloque_jusqua"] - t + 0.999))

    def enregistrer_echec(self, identifiant, maintenant=None):
        """Note un échec. Retourne les secondes de blocage si l'identifiant
        vient d'être bloqué, sinon 0."""
        t = time.time() if maintenant is None else maintenant
        with self._verrou:
            if len(self._donnees) > self.max_entrees:
                self._nettoyer(t)
            cle = self._cle(identifiant)
            e = self._donnees.setdefault(cle, {"n": 0, "dernier": 0.0, "bloque_jusqua": 0.0})
            if t - e["dernier"] > self.fenetre:
                e["n"] = 0
            e["n"] += 1
            e["dernier"] = t
            if e["n"] >= self.seuil:
                e["n"] = 0
                e["bloque_jusqua"] = t + self.duree_blocage
                return self.duree_blocage
            return 0

    def reinitialiser(self, identifiant):
        """Efface le compteur (après une connexion réussie)."""
        with self._verrou:
            self._donnees.pop(self._cle(identifiant), None)

    def _nettoyer(self, t):
        """Supprime les entrées périmées (appelé sous verrou)."""
        for cle in [
            c for c, e in self._donnees.items()
            if e["bloque_jusqua"] < t and t - e["dernier"] > self.fenetre
        ]:
            del self._donnees[cle]
