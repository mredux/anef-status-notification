# ANEF Bot — anef-status-notification

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
2. Ajoutez un ou plusieurs utilisateurs dans la liste `users` de `config.json` :

   ```json
   {
       "users": [
           {
               "anef_username": "votre_numero",
               "anef_password": "votre_mot_de_passe",
               "wa_phone": "+33xxxxxxxxx",
               "wa_apikey": "votre_cle_api_callmebot"
           }
       ]
   }
   ```

   Vous pouvez aussi passer ces valeurs via des variables d'environnement :
   `ANEF_USER`, `ANEF_PASS`, `WA_PHONE`, `WA_APIKEY` (pour l'utilisateur unique par défaut).

## Utilisation

```bash
python bot_anef.py
```

Pour voir le navigateur (mode non headless) :
```bash
python bot_anef.py --visible
```

## Fonctionnement

Pour chaque utilisateur dans `config.json` :
1. Se connecte au SSO ANEF avec ses identifiants
2. Récupère le statut de sa demande de titre de séjour
3. Compare avec le dernier statut connu (stocké par utilisateur dans `anef_state.json`)
4. Envoie une notification WhatsApp via [CallMeBot](https://www.callmebot.com/blog/free-api-whatsapp-messages/) si le statut a changé

## Licence

MIT
