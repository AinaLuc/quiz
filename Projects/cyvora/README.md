# Cyvora

Application `Next.js + Supabase Auth` pour `Cyvora`, une IA réceptionniste HVAC au Québec.

## Inclus

- Landing page en français
- Connexion avec courriel/mot de passe
- Inscription avec essai gratuit de 10 jours
- Connexion et inscription avec Google via Supabase OAuth
- Dashboard protégé avec métriques principales
- Gestion simple de l'essai gratuit basée sur une société créée dans Supabase
- Webhook Vapi vers Supabase pour afficher les appels et rendez-vous
- Webhook Retell vers Supabase pour afficher les appels et rendez-vous

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

## 5. Connecter Vapi

Configurez le Server URL de Vapi vers:

```text
https://votre-domaine.com/api/vapi
```

En local, utilisez un tunnel public puis pointez Vapi vers ce tunnel. Vapi documente `ngrok` et `vapi listen` pour le développement local:

- https://docs.vapi.ai/cli/webhook
- https://docs.vapi.ai/server-url/events

Ajoutez aussi un secret partagé côté Vapi avec `Authorization: Bearer ...` ou `X-Vapi-Secret`, puis utilisez la même valeur dans `VAPI_WEBHOOK_SECRET`.

Le flux est:

1. Vapi envoie les événements de call à `/api/vapi`
2. L'API route insère ou met à jour `calls`
3. Si le payload indique un rendez-vous confirmé, l'API route crée ou met à jour `appointments`
4. Le dashboard lit directement Supabase

Si vous gérez plusieurs entreprises, ajoutez `companyId` dans les metadata de vos appels Vapi pour router les appels vers la bonne société.

## 5b. Connecter Retell AI

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
5. Le dashboard lit directement Supabase

Si vous gérez plusieurs entreprises, ajoutez `companyId` dans `metadata` côté Retell pour router les appels vers la bonne société.

Important:

- Retell demande le corps brut pour vérifier la signature.
- Selon la documentation Retell, il faut utiliser une API key avec badge webhook pour la vérification.
- Le sélecteur de numéros dans le dashboard est encore branché sur Vapi. Cette mise à jour ajoute le webhook Retell, pas encore la gestion des numéros Retell.

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
- Mapper explicitement les `structuredData` Vapi vers vos champs métier HVAC
- Ajouter l'affichage des transcriptions et résumés d'appel
- Ajouter rôles équipe / admin
