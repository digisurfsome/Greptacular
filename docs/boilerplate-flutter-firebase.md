# Boilerplate Analysis: apparence-kit-firebase

> **Source:** `github.com/digisurfsome/apparence-kit-firebase`
> **Stack:** Flutter + Dart + Firebase + Riverpod + RevenueCat + Mixpanel + Sentry + GoRouter
> **Purpose:** Pre-built foundation for mobile applications (iOS + Android)

---

## What's Already Built

### Authentication (Firebase Auth)
- Email/password signup + login
- OAuth providers (Google, Apple Sign-In)
- Phone number verification
- Session persistence
- Password reset flow
- Onboarding flow with profile setup

### Database (Cloud Firestore)
- Firestore client configuration
- Security rules
- User document with profile data
- Collection structure for app data

### Payments (RevenueCat)
- In-app purchase integration
- Subscription management
- Entitlement checking
- Paywall UI components
- Receipt validation

### Analytics (Mixpanel)
- Mixpanel client initialization
- Screen view tracking
- Custom event tracking
- User property setting
- Funnel tracking helpers

### Error Tracking (Sentry)
- Sentry Flutter SDK initialization
- Automatic crash reporting
- Custom error boundaries
- Performance monitoring

### Navigation (GoRouter)
- Declarative routing configuration
- Deep link handling
- Auth-aware route guards
- Nested navigation support
- Transition animations

### State Management (Riverpod)
- Provider architecture setup
- Auth state providers
- User profile providers
- Theme and locale providers

---

## File Structure

```
├── lib/
│   ├── main.dart                    # App entry point
│   ├── app/
│   │   ├── app.dart                 # MaterialApp configuration
│   │   └── router.dart              # GoRouter route definitions
│   ├── features/
│   │   ├── auth/
│   │   │   ├── data/
│   │   │   │   ├── auth_repository.dart
│   │   │   │   └── user_repository.dart
│   │   │   ├── domain/
│   │   │   │   └── user_model.dart
│   │   │   └── presentation/
│   │   │       ├── login_screen.dart
│   │   │       ├── signup_screen.dart
│   │   │       └── onboarding_screen.dart
│   │   ├── home/
│   │   │   └── presentation/
│   │   │       └── home_screen.dart
│   │   ├── settings/
│   │   │   └── presentation/
│   │   │       └── settings_screen.dart
│   │   └── subscription/
│   │       ├── data/
│   │       │   └── subscription_repository.dart
│   │       └── presentation/
│   │           └── paywall_screen.dart
│   ├── core/
│   │   ├── constants/
│   │   │   └── app_constants.dart
│   │   ├── theme/
│   │   │   ├── app_theme.dart
│   │   │   └── app_colors.dart
│   │   ├── utils/
│   │   │   ├── analytics.dart       # Mixpanel helpers
│   │   │   └── error_handler.dart   # Sentry helpers
│   │   └── providers/
│   │       ├── auth_provider.dart
│   │       └── user_provider.dart
│   └── shared/
│       ├── widgets/
│       │   ├── app_button.dart
│       │   ├── app_text_field.dart
│       │   └── loading_overlay.dart
│       └── extensions/
│           └── context_extensions.dart
├── android/
│   └── app/
│       └── build.gradle
├── ios/
│   └── Runner/
│       └── Info.plist
├── test/
│   └── widget_test.dart
├── pubspec.yaml
├── firebase.json
├── firestore.rules
└── firestore.indexes.json
```

---

## Database Schema (Firestore)

### `users` collection
| Field | Type | Notes |
|-------|------|-------|
| uid | string | Firebase Auth UID (document ID) |
| email | string | From Firebase Auth |
| displayName | string | Set during onboarding |
| photoURL | string | Profile picture URL |
| subscriptionStatus | string | active, expired, free |
| revenueCatId | string | RevenueCat customer ID |
| createdAt | timestamp | |
| updatedAt | timestamp | |
| fcmToken | string | Push notification token |
| onboardingComplete | boolean | |

### Security Rules
- Users can only read/write their own document
- Admin SDK has full access
- Subcollections inherit parent document permissions

---

## Navigation Routes Already Built

| Path | Screen | Auth Required | Notes |
|------|--------|---------------|-------|
| /login | LoginScreen | No | |
| /signup | SignupScreen | No | |
| /onboarding | OnboardingScreen | Yes | First-time only |
| /home | HomeScreen | Yes | Main app screen |
| /settings | SettingsScreen | Yes | |
| /paywall | PaywallScreen | Yes | RevenueCat paywall |

---

## Auth Flow

1. User opens app -> GoRouter checks auth state
2. No session -> redirect to `/login`
3. User signs up -> Firebase creates user + Firestore document
4. Onboarding screen collects profile data
5. `onboardingComplete: true` set -> redirect to `/home`
6. Session persists via Firebase Auth SDK
7. Token refresh handled automatically

---

## What Needs Connecting (for dual builds)

When merging with the web app:
1. **Shared backend** — mobile talks to Supabase via REST/Realtime, not Firestore
2. **Auth bridge** — either use Supabase Auth for mobile too (replace Firebase Auth) OR sync users between Firebase Auth and Supabase Auth
3. **Payments** — RevenueCat handles mobile purchases; Stripe handles web. Both need to update the same user profile in Supabase
4. **Analytics** — Mixpanel for mobile, PostHog for web. Can bridge via user ID matching
5. **Push notifications** — Firebase Cloud Messaging stays for mobile, web uses browser notifications

### Recommended Merge Strategy
- **Option A (Supabase everywhere):** Replace Firebase Auth + Firestore with Supabase client for Flutter. Keeps one auth system, one database.
- **Option B (Firebase for mobile, Supabase for web):** Sync user records via cloud functions. More complex but preserves native mobile experience.

---

## Environment Variables / Configuration Required

### Firebase
```
// google-services.json (Android)
// GoogleService-Info.plist (iOS)
// firebase_options.dart (generated by FlutterFire CLI)
```

### RevenueCat
```
REVENUECAT_API_KEY_IOS=
REVENUECAT_API_KEY_ANDROID=
```

### Mixpanel
```
MIXPANEL_TOKEN=
```

### Sentry
```
SENTRY_DSN=
```
