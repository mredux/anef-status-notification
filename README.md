# ANEF Bot

Surveille l'évolution d'une demande de titre de séjour sur le site [ANEF](https://administration-etrangers-en-france.interieur.gouv.fr/) et envoie une notification WhatsApp en cas de changement de statut.

## Prérequis

- Python 3.8+
- Chrome installé

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Copiez le fichier de configuration :
   ```bash
   cp config.example.json config.json
   ```
2. Remplissez `config.json` avec vos informations (numéro étranger, mot de passe ANEF, téléphone et clé API CallMeBot).

   Vous pouvez aussi passer ces valeurs via des variables d'environnement :
   `ANEF_USER`, `ANEF_PASS`, `WA_PHONE`, `WA_APIKEY`.

## Utilisation

```bash
python bot_anef.py
```

Pour voir le navigateur (mode non headless) :
```bash
python bot_anef.py --visible
```

## Fonctionnement

1. Se connecte au SSO ANEF avec vos identifiants
2. Récupère le statut de votre demande de titre de séjour
3. Compare avec le dernier statut connu (stocké dans `anef_state.json`)
4. Envoie une notification WhatsApp via [CallMeBot](https://www.callmebot.com/blog/free-api-whatsapp-messages/) si le statut a changé

## Licence

MIT
