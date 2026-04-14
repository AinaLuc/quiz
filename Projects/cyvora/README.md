# Cyvora

Application `Next.js + Supabase Auth` pour `Cyvora`, une IA réceptionniste HVAC au Québec.

## Inclus

- Landing page en français
- Connexion avec courriel/mot de passe
- Inscription avec essai gratuit de 10 jours
- Connexion et inscription avec Google via Supabase OAuth
- Dashboard protégé avec métriques principales
- Gestion simple de l'essai gratuit basée sur une société créée dans Supabase
- Webhook Retell vers Supabase pour afficher les appels et rendez-vous
- Inventaire Retell des numéros avec assignation par société

## 1. Installer les dépendances

```bash
cd /Users/mac/Projects/cyvora
npm install
```

## 2. Configurer les variables d'environnement

Copier `.env.example` vers `.env.local` et remplir:

```bash
cp .env.example .env.local
```

Variables requises:

- `NEXT_PUBLIC_SITE_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `RETELL_API_KEY`
- `RETELL_TEMPLATE_AGENT_ID` (optionnel, agent modèle dupliqué pour chaque client)
- `RETELL_INBOUND_COMPANY_ID`
- `RETELL_INBOUND_AGENT_ID` (optionnel)
- `RETELL_INBOUND_PHONE_NUMBER` (optionnel)
- `RETELL_INBOUND_NUMBER_MAP` (optionnel, JSON pour multi-numéros)
- `VAPI_WEBHOOK_SECRET`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID`
- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
- `CRON_SECRET`

## 3. Configurer Supabase Auth

Dans Supabase:

1. Activer `Email` dans Authentication.
2. Activer `Google` dans Authentication > Providers.
3. Ajouter l'URL de redirection:

```text
http://localhost:3000/auth/callback
```

Si vous déployez plus tard, ajoutez aussi l'URL de production, par exemple:

```text
https://votre-domaine.com/auth/callback
```

## 3b. Créer les tables Postgres

Dans Supabase, ouvrez `SQL Editor`, puis exécutez le contenu de:

[`supabase/schema.sql`](/Users/mac/Projects/cyvora/supabase/schema.sql)

Ce script crée:

- `public.companies`
- `public.profiles`
- `public.calls`
- `public.appointments`
- `public.subscriptions`
- `public.retell_phone_assignments`
- `public.companies.retell_agent_id`
- `public.companies.retell_llm_id`
- `public.companies.retell_base_general_prompt`
- les politiques RLS
- un trigger qui crée automatiquement une entreprise et un profil lors d'un nouveau signup

Sans ce script, l'utilisateur peut se connecter, mais aucune donnée métier n'est écrite dans Postgres.

## 4. Lancer l'application

```bash
npm run dev
```

Puis ouvrir:

```text
http://localhost:3000
```

## 5. Connecter Retell AI

Configurez le `Agent Level Webhook URL` de Retell vers:

```text
https://votre-domaine.com/api/retell
```

En local, utilisez un tunnel public:

```text
https://votre-tunnel-public/api/retell
```

Le flux est:

1. Retell envoie `call_started`, `call_ended` et `call_analyzed` à `/api/retell`
2. L'API route vérifie `x-retell-signature` avec `RETELL_API_KEY`
3. L'API route insère ou met à jour `calls`
4. Si `call_analysis.custom_analysis_data` ou les variables collectées indiquent un rendez-vous confirmé, l'API route crée ou met à jour `appointments`
5. Le dashboard lit directement Supabase pour les appels et l'assignation des numéros

Si vous gérez plusieurs entreprises, ajoutez `companyId` dans `metadata` côté Retell pour router les appels vers la bonne société.

Important:

- Retell demande le corps brut pour vérifier la signature.
- Selon la documentation Retell, il faut utiliser une API key avec badge webhook pour la vérification.
- Pour les appels entrants, vous pouvez configurer le numéro Retell avec un `Inbound Call Webhook URL` vers `https://votre-domaine.com/api/retell/inbound`.
- Cette route résout d'abord le `to_number` dans la table `retell_phone_assignments`, puis renvoie `call_inbound.metadata.companyId`.
- Si aucun enregistrement n'existe, elle retombe sur `RETELL_INBOUND_COMPANY_ID` et `RETELL_INBOUND_NUMBER_MAP`.
- `RETELL_INBOUND_PHONE_NUMBER` reste un fallback d'affichage.
- Le dashboard utilise la liste live des numéros Retell et stocke seulement les assignations par société dans `retell_phone_assignments`.
- Lors de l'assignation d'un numéro, l'application duplique l'agent modèle Retell, injecte le nom de l'entreprise dans le prompt en français canadien, puis lie le numéro à cet agent.

## 6. Connecter Stripe

Ce projet inclut:

- un checkout Stripe sur `/api/stripe/checkout`
- un webhook Stripe sur `/api/stripe/webhook`
- un tableau `subscriptions`
- un état de facturation sur `companies`

Flux:

1. l'utilisateur clique sur le bouton d'upgrade dans le dashboard
2. l'app crée une session Stripe Checkout
3. Stripe redirige l'utilisateur vers le paiement
4. Stripe appelle `/api/stripe/webhook`
5. l'abonnement et l'état de facturation sont mis à jour dans Supabase

Variables requises:

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
```

Le plan recommandé est de laisser l'utilisateur upgrader pendant l'essai et de laisser Stripe commencer la facturation à la fin du trial si la date de fin d'essai est encore dans le futur.

## 7. Emails de cycle de vie

Le projet inclut maintenant:

- un rappel automatique dans les `3 derniers jours` d'essai
- un email automatique une fois l'essai expiré
- une bannière dashboard avec bouton d'upgrade pendant la phase critique

Variables requises:

```env
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=notifications@votre-domaine.com
CRON_SECRET=une_valeur_longue_et_aleatoire
```

Le job quotidien est exposé sur:

```text
/api/cron/trial-notifications
```

Si vous déployez sur Vercel, le fichier [`vercel.json`](/Users/mac/Projects/cyvora/vercel.json) planifie déjà ce job une fois par jour.

## Flux Google réel

Le bouton Google utilise `supabase.auth.signInWithOAuth({ provider: "google" })`.

Le flux est:

1. L'utilisateur clique sur Google
2. Il est redirigé vers Google
3. Google revient sur `/auth/callback`
4. La session Supabase est créée
5. L'utilisateur arrive sur `/dashboard`

## Suite recommandée

- Ajouter Stripe pour le passage après essai gratuit
- Mapper explicitement les `structuredData` Retell vers vos champs métier HVAC
- Ajouter l'affichage des transcriptions et résumés d'appel
- Ajouter rôles équipe / admin
