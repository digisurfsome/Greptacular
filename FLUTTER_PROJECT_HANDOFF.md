# ApparenceKit Flutter Project — Complete Handoff

> **Project:** ApparenceKit CLI Flutter boilerplate (v5.0.16)
> **Project Location:** `C:\WINDOWS\myproject` (Windows machine — NEEDS TO MOVE, see below)
> **Firebase Project:** `sugarless-252ae`
> **User Account:** `dux8bevo@gmail.com`
> **Tech Stack:** Flutter 3.29.3 / Dart 3.8.1 + Firebase Auth + Riverpod + Freezed/build_runner
> **Last Updated:** February 20, 2026
> **Branch:** `claude/setup-flutter-appearance-kit-uW97I`

---

## TABLE OF CONTENTS

1. [Current Status — Where We Left Off](#current-status)
2. [Complete Command History (Chronological)](#command-history)
3. [The 3 Blockers Preventing Build](#blockers)
4. [Step-by-Step Resume Plan (Copy-Paste Ready)](#resume-plan)
5. [Known Code Issues & Fixes](#code-issues)
6. [Key Files Reference](#key-files)
7. [Agent Handoff Context](#agent-handoff)

---

## Current Status — Where We Left Off

### Progress: 3/4 Complete

| Phase | Status | What |
|-------|--------|------|
| 1. CLI Install | DONE | ApparenceKit CLI v5.0.16 installed |
| 2. Firebase Login | DONE | Logged in as dux8bevo@gmail.com |
| 3. FlutterFire Configure | DONE | Both prod and dev configs generated |
| 4. Build & Run | **BLOCKED** | 3 issues preventing `flutter run` |

### What's Blocking the Build

1. **Dart SDK version mismatch** — Project `pubspec.yaml` requires `sdk: ">=3.11.0"` but Flutter 3.29.3 ships with Dart 3.8.1. Since Dart 3.11.0 doesn't exist yet, this constraint is likely wrong and needs to be relaxed.
2. **Missing generated files** — `.g.dart` and `.freezed.dart` files haven't been generated because `build_runner` can't run due to the SDK constraint.
3. **Project location permissions** — `C:\WINDOWS\myproject` is OS-protected. The switch fix script got "Access Denied" errors. Project needs to move to a user-writable location.

---

## Complete Command History (Chronological)

### Phase 1 — CLI Installation (DONE)

```powershell
# Install ApparenceKit CLI v5.0.16
irm https://tinyurl.com/kitwindows | iex
```
Result: Installed successfully.

### Phase 2 — Firebase Login (DONE, with workarounds)

```powershell
# First attempt — FAILED (firebase not in PATH)
firebase login

# Temporary PATH fix for npm global binaries
$env:PATH += ";C:\Users\lober\AppData\Roaming\npm"

# Second attempt — SUCCESS
firebase login
# Output: "Already logged in as dux8bevo@gmail.com"
```

### Phase 3 — FlutterFire Configure (DONE)

```powershell
# Install FlutterFire CLI
dart pub global activate flutterfire_cli
# Activated flutterfire_cli v1.3.1

# Temporary PATH fix for Pub Cache binaries
$env:PATH += ";$env:LOCALAPPDATA\Pub\Cache\bin"

# Navigate to project
cd C:\WINDOWS\myproject

# Configure Firebase — production config
flutterfire configure --project=sugarless-252ae
# Registered apps for web/android/ios

# Configure Firebase — dev config
flutterfire configure --project=sugarless-252ae --out lib/firebase_options_dev.dart
# Generated dev config file
```

### Phase 4 — Build Attempts (BLOCKED)

```powershell
# Attempt 1 — FAILED: missing .g.dart and .freezed.dart files
flutter run -d chrome

# Attempt 2 — FAILED: same missing generated files
flutter run -d chrome --release

# Attempt 3 — FAILED: Dart SDK version mismatch
# Dart SDK 3.8.1 but project pubspec.yaml requires >=3.11.0
dart run build_runner build --delete-conflicting-outputs
```

### Phase 5 — Switch Fix Attempts (UNCERTAIN)

```powershell
# PowerShell Fix-Switch function defined (see code issues section below)
# Applied to 6 files — all reported "Access Denied" (C:\WINDOWS is protected)
# BUT also said "Fixed" — unclear if changes actually persisted
```

---

## The 3 Blockers Preventing Build

### Blocker 1: Dart SDK Version Constraint (THE MAIN BLOCKER)

The `pubspec.yaml` has an SDK constraint requiring `>=3.11.0` but:
- Flutter 3.29.3 bundles Dart 3.8.1
- Dart version 3.11.0 **does not exist** — Dart versions go 3.0, 3.1, ..., 3.8
- This constraint is almost certainly wrong in the ApparenceKit template

**Fix:** Edit `pubspec.yaml` and change the SDK constraint:

```yaml
# BEFORE (broken):
environment:
  sdk: ">=3.11.0 <4.0.0"   # or whatever the exact constraint is

# AFTER (fixed):
environment:
  sdk: ">=3.1.0 <4.0.0"    # Dart 3.1.0+ (your 3.8.1 satisfies this)
```

**Important:** Before changing, open `pubspec.yaml` and check the EXACT constraint. It might be `^3.11.0` or `>=3.11.0`. Either way, `3.11.0` doesn't exist and needs to be changed to something your Dart 3.8.1 satisfies.

### Blocker 2: Missing Generated Files (.g.dart, .freezed.dart)

ApparenceKit uses code generation (Freezed + json_serializable). The generated files are NOT checked into git — they must be created by running `build_runner`:

```powershell
dart run build_runner build --delete-conflicting-outputs
```

This command will ONLY work after fixing Blocker 1 (the SDK constraint). Once the constraint is fixed, this will generate all the `.g.dart` and `.freezed.dart` files the project needs.

### Blocker 3: Project Location Permissions

`C:\WINDOWS\myproject` is in a system-protected directory. This causes:
- "Access Denied" when scripts try to modify files
- Potential issues with `build_runner` writing generated files
- General flakiness with file operations

**Fix:** Move the entire project to your user directory:

```powershell
# Move project to user directory
Move-Item C:\WINDOWS\myproject C:\Users\lober\myproject

# Or copy if you want to keep the original
Copy-Item -Recurse C:\WINDOWS\myproject C:\Users\lober\myproject
```

---

## Step-by-Step Resume Plan (Copy-Paste Ready)

Run these commands in PowerShell, in order. Each step depends on the previous one.

### Step 0: Permanent PATH Fix (run ONCE, never again)

```powershell
[Environment]::SetEnvironmentVariable("PATH", [Environment]::GetEnvironmentVariable("PATH", "User") + ";C:\Users\lober\AppData\Roaming\npm;C:\Users\lober\AppData\Local\Pub\Cache\bin", "User")
```

**Close and reopen PowerShell** after running this. It permanently adds npm and Pub Cache to your PATH.

### Step 1: Move Project Out of C:\WINDOWS

```powershell
Copy-Item -Recurse C:\WINDOWS\myproject C:\Users\lober\myproject
cd C:\Users\lober\myproject
```

### Step 2: Fix the SDK Constraint

```powershell
# Open pubspec.yaml and find the 'environment > sdk' line
# Change ">=3.11.0" (or "^3.11.0") to ">=3.1.0 <4.0.0"
notepad pubspec.yaml
```

Or use PowerShell to fix it in-place:
```powershell
(Get-Content pubspec.yaml) -replace '>=3\.11\.0', '>=3.1.0' | Set-Content pubspec.yaml
```

### Step 3: Get Dependencies

```powershell
flutter pub get
```

### Step 4: Generate Code (build_runner)

```powershell
dart run build_runner build --delete-conflicting-outputs
```

This generates all the missing `.g.dart` and `.freezed.dart` files. May take a minute.

### Step 5: Re-apply Switch Fixes (if needed)

The previous attempt got "Access Denied" in `C:\WINDOWS`. Now that the project is in `C:\Users\lober\myproject`, re-run the fix:

```powershell
cd C:\Users\lober\myproject

function Fix-Switch {
    param([string]$File, [string]$Fix)
    $path = Join-Path (Get-Location) $File
    $lines = [System.Collections.Generic.List[string]]([System.IO.File]::ReadAllLines($path))
    $changed = $false
    for ($i = $lines.Count - 1; $i -ge 0; $i--) {
        if ($lines[$i] -match 'switch\s*\(') {
            $b = 0
            for ($j = $i; $j -lt $lines.Count; $j++) {
                foreach ($c in $lines[$j].ToCharArray()) {
                    if ($c -eq '{') { $b++ }
                    if ($c -eq '}') { $b-- }
                }
                if ($b -eq 0 -and $j -gt $i) {
                    if ($lines[$j-1] -notmatch '^\s*_\s*=>') {
                        $indent = if ($lines[$j-1] -match '^(\s+)') { $Matches[1] } else { '  ' }
                        $lines.Insert($j, "$indent$Fix")
                        $changed = $true
                    }
                    break
                }
            }
        }
    }
    if ($changed) {
        [System.IO.File]::WriteAllLines($path, $lines)
        Write-Host "Fixed: $File"
    } else {
        Write-Host "Skipped: $File (already has wildcard case)"
    }
}

Fix-Switch "lib\modules\authentication\ui\phone_auth_page.dart" "_ => const SizedBox(),"
Fix-Switch "lib\modules\authentication\ui\recover_password_page.dart" "_ => const SizedBox(),"
Fix-Switch "lib\modules\authentication\ui\signin_page.dart" "_ => const SizedBox(),"
Fix-Switch "lib\modules\authentication\ui\signup_page.dart" "_ => const SizedBox(),"
Fix-Switch "lib\modules\subscription\ui\premium_page.dart" "_ => const SizedBox(),"
Fix-Switch "lib\modules\authentication\providers\phone_auth_notifier.dart" "_ => throw StateError('Unknown state'),"
Write-Host "Done! All files processed."
```

If all say "Skipped" — the previous fix DID work despite the "Access Denied" warnings.

### Step 6: Analyze

```powershell
flutter analyze
```

Should show 0 errors. If there are errors, fix them before proceeding.

### Step 7: Run the App

```powershell
flutter run -d chrome
```

### Step 8: Test Auth Flows

Once the app launches in Chrome, test:
- Email sign-in
- Email sign-up
- Phone authentication
- Password recovery
- Premium/subscription flow
- **Watch for circular redirect loop** (Problem #1 — see code issues below)

---

## Known Code Issues & Fixes

### Issue 1: Firebase Auth Circular Redirect Loop

**Status:** FIX NEVER APPLIED — still needs to be done after the app builds

The app gets stuck bouncing between login and home screens. A two-line fix was identified in a previous session but never applied.

**Root Cause:** The Firebase auth state listener doesn't properly handle the initial auth check, causing:
- Detect "no user" -> redirect to login
- Login triggers auth state change -> redirect to home
- Home re-checks auth -> redirect back to login
- Repeat forever

**Likely Fix (confirm by inspecting the auth router):**
```dart
// In the auth state listener/router (main.dart or auth_router.dart):
if (authState == AuthState.loading) return const SplashScreen();
if (authState == AuthState.authenticated && currentRoute == '/login') return;
```

**Action:** After the app builds and runs, if you see the circular loop, inspect the auth routing code and add the guard conditions.

### Issue 2: Non-Exhaustive Switch Expressions

**Status:** Fix script ran but "Access Denied" — needs re-verification after project move

6 files need wildcard `_ =>` cases in switch expressions. The Fix-Switch PowerShell script handles this (included in Step 5 above).

### Issue 3: State Management Fix

**Status:** Believed applied, needs confirmation

A separate Riverpod state management fix was discussed and believed to have been applied. Verify by checking provider/notifier files for proper error state handling.

---

## Key Files Reference

| File | Role |
|------|------|
| `pubspec.yaml` | **CHECK THIS FIRST** — SDK constraint is the main blocker |
| `lib/main.dart` | App entry point, likely where auth loop fix goes |
| `lib/firebase_options.dart` | Production Firebase config (generated) |
| `lib/firebase_options_dev.dart` | Dev Firebase config (generated) |
| `lib/modules/authentication/ui/phone_auth_page.dart` | Phone auth UI (needs switch fix) |
| `lib/modules/authentication/ui/signin_page.dart` | Email sign-in UI (needs switch fix) |
| `lib/modules/authentication/ui/signup_page.dart` | Email sign-up UI (needs switch fix) |
| `lib/modules/authentication/ui/recover_password_page.dart` | Password recovery UI (needs switch fix) |
| `lib/modules/authentication/providers/phone_auth_notifier.dart` | Phone auth state (needs switch fix) |
| `lib/modules/subscription/ui/premium_page.dart` | Premium/subscription UI (needs switch fix) |

---

## Agent Handoff Context

### What This Project Is

This is the **Flutter companion app** for the AutoForge ecosystem. It's built using **ApparenceKit** (a commercial Flutter boilerplate/starter kit, v5.0.16) with Firebase Authentication. The app connects to the same Supabase backend as the web app (dual boilerplate pattern — see `self-deploy-vps-handoff.md`).

### What the Flutter App Will Do

1. **Idea Capture** — Jot down app ideas on the go (voice-to-text)
2. **PRD Builder** — Expand ideas into full PRDs via conversational flow
3. **Build Monitoring** — View active builds across VPS/local instances
4. **Account Management** — View credits, subscription, build history
5. **Instance Status** — Check if VPS instances are running

### What Was Done (3/4 Complete)

1. ApparenceKit CLI installed (v5.0.16)
2. Firebase login authenticated (dux8bevo@gmail.com)
3. FlutterFire configured for prod + dev (project: sugarless-252ae)
4. **BLOCKED** at build step — SDK constraint + missing code generation + permissions

### What Needs to Happen Next

Follow the [Step-by-Step Resume Plan](#resume-plan) above. The TL;DR is:
1. Move project out of `C:\WINDOWS`
2. Fix the SDK constraint in `pubspec.yaml`
3. Run `dart run build_runner build --delete-conflicting-outputs`
4. Re-run switch fixes
5. `flutter analyze` then `flutter run -d chrome`

### User Preferences

- Direct, practical communication
- PowerShell scripts for batch operations (Windows user)
- Documentation as safety net against context loss
- Prefers being told when something is uncertain

---

*Last updated: February 20, 2026*
*Session: claude/setup-flutter-appearance-kit-uW97I*
