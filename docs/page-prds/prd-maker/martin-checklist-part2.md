# Martin's Build PRD -- Technical Checklist (Section 4: Lines 800-1500)

Extracted from `3-MARTINS-MAIN-BUILD-PRD.txt`, lines 800-1500. Every technical instruction, rule, pattern, and preference is captured below.

---

### Data/API Patterns

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Delete account removes subcollections | "Delete all documents in each subcollection" | `deleteUserAccount(uid, subcollections)` iterates subcollection names, calls `getDocs` then `deleteDoc` on every doc via `Promise.all`, then deletes the parent `users/{uid}` document. | _[to be filled]_ |
| 2 | Subcollection list is explicit | "List all subcollections your app uses" | Pass an explicit string array of subcollection names (e.g. `['items', 'settings']`) to the delete function -- no dynamic discovery. | _[to be filled]_ |
| 3 | Realtime subscription pattern | "For realtime updates ... return onSnapshot(q, ...)" | Use `onSnapshot` with a query ordered by `createdAt desc`; map snapshot docs to `{ id: doc.id, ...doc.data() }` and pass to callback. Return the unsubscribe function. | _[to be filled]_ |
| 4 | CRUD helper layer | Code block showing `addDocument`, `updateDocument`, `deleteDocument`, `getDocuments` | Wrap all Firestore operations in a `services/firestore.ts` helper module. Every write sets `updatedAt: serverTimestamp()`; creates also set `createdAt: serverTimestamp()`. | _[to be filled]_ |
| 5 | Documents always include timestamps | "createdAt: serverTimestamp(), updatedAt: serverTimestamp()" | Every Firestore document must have `createdAt` (set on create) and `updatedAt` (set on create and every update) using `serverTimestamp()`. | _[to be filled]_ |
| 6 | Default sort order | "orderBy('createdAt', 'desc')" | All collection queries default to `orderBy('createdAt', 'desc')` -- newest first. | _[to be filled]_ |
| 7 | List pagination is mandatory | "Lists MUST handle large amounts of data" | Every list view must implement one of: pagination (10-20 items per page), load-more button, or infinite scroll via Intersection Observer. Pick ONE and use it consistently. | _[to be filled]_ |
| 8 | Pagination controls pattern | "Show 10-20 items per page ... Pagination controls at bottom" | Use `ITEMS_PER_PAGE = 10` constant, `page` state starting at 1, Previous/Next buttons disabled at bounds, "Page X of Y" label centered between buttons. | _[to be filled]_ |
| 9 | Load-more shows remaining count | "Load More ({remaining} remaining)" | Load-more button must display how many items remain unloaded. Initial `limit` state of 10, increment by 10 on click. | _[to be filled]_ |

---

### Authentication/Security

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Delete account requires typed confirmation | "Type DELETE to confirm" | Delete account flow requires user to type the exact string `"DELETE"` into a text input. Submit button is `disabled` until `confirmText !== 'DELETE'`. | _[to be filled]_ |
| 2 | Delete button disabled during operation | "disabled={confirmText !== 'DELETE' \|\| isDeleting}" | Delete confirmation button must check both confirmation text match AND `isDeleting` state. Show `"Deleting..."` text while in progress. | _[to be filled]_ |
| 3 | Logout after account deletion | "await deleteUserAccount(user.uid, ...); await logout();" | After successful account deletion, immediately call `logout()` to clear the auth session before showing success toast. | _[to be filled]_ |
| 4 | Protected routes wrap layout | "ProtectedRoute > Layout > Page" | All authenticated pages must be wrapped as `<ProtectedRoute><Layout><Page /></Layout></ProtectedRoute>`. Public pages (landing, login) have no wrapper. | _[to be filled]_ |
| 5 | Auth/theme/toast providers wrap router | "AuthProvider > ThemeProvider > ToastProvider > BrowserRouter" | Provider nesting order (outermost to innermost): `AuthProvider` > `ThemeProvider` > `ToastProvider` > `BrowserRouter` > `Routes`. | _[to be filled]_ |
| 6 | Admin-only nav items are conditional | "isAdmin && <Link to='/admin'>Admin</Link>" | Sidebar navigation must conditionally render admin links based on an `isAdmin` flag. | _[to be filled]_ |

---

### Database/Storage

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | User data in subcollections | "getUserCollection(uid, collectionName)" | All user-owned data lives under `users/{uid}/{collectionName}/{docId}`. Use a helper that returns `collection(db, 'users', uid, collectionName)`. | _[to be filled]_ |
| 2 | Delete cascades to subcollections | "removes user profile and all subcollections" | Account deletion must delete all documents in every known subcollection BEFORE deleting the parent user profile document. | _[to be filled]_ |
| 3 | Batch deletes via Promise.all | "const deletePromises = snapshot.docs.map(doc => deleteDoc(doc.ref)); await Promise.all(deletePromises);" | Subcollection deletion fetches all docs, maps to `deleteDoc` promises, then awaits `Promise.all` for each subcollection sequentially. | _[to be filled]_ |

---

### Error Handling

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Delete failure keeps modal open | "catch (error) { showToast({ type: 'error', message: 'Failed to delete account' }); setIsDeleting(false); }" | On delete error: show error toast, reset `isDeleting` to false, do NOT close modal, do NOT navigate away. | _[to be filled]_ |
| 2 | Success feedback is toast + navigate | "Show success Toast ... Navigate to appropriate view" | Every successful mutation: show a success toast with descriptive message, then navigate to the next logical view. | _[to be filled]_ |
| 3 | Error feedback preserves form state | "Show error Toast with helpful message ... Stay on current view ... Keep form data intact" | On error: show error toast, remain on current view, do NOT clear or reset form data. | _[to be filled]_ |
| 4 | Delete flow is 6-step | "1. User clicks delete 2. ConfirmModal appears ... 3. User confirms 4. Show loading state on button 5. On success: Toast + redirect to List 6. On error: Toast + close modal" | Delete flow: click > ConfirmModal > confirm > button loading spinner + disabled > success toast + redirect to list view, OR error toast + close modal. | _[to be filled]_ |
| 5 | Loading states match content shape | "Lists: Show Skeleton cards (not spinner) ... Detail View: Show Skeleton matching content layout ... Buttons during action: Show spinner inside button, disable button" | Lists show skeleton cards, detail views show skeleton matching layout, action buttons show inline spinner and become disabled. Never use bare text "Loading...". | _[to be filled]_ |

---

### Performance

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Animations use short durations | "transition-opacity duration-200 ... transition-all duration-200 ease-out ... transition-transform duration-300 ease-out ... transition-all duration-150" | Modal backdrop: 200ms opacity. Modal content: 200ms ease-out. Toast: 300ms ease-out. Card hover: 200ms. Button press: 150ms. Never exceed 300ms for UI transitions. | _[to be filled]_ |
| 2 | Card hover uses translate not box-shadow alone | "hover:shadow-md hover:-translate-y-0.5" | Card hover effect combines `shadow-md` with `translateY(-0.5)` for a lift effect. Use `transition-all duration-200`. | _[to be filled]_ |
| 3 | Button press uses scale | "active:scale-[0.98]" | Buttons must have `active:scale-[0.98]` with `transition-all duration-150` for tactile feedback on click. | _[to be filled]_ |
| 4 | Choose one pagination strategy | "Choose ONE approach and implement it consistently" | Pick one list-handling strategy (pagination, load-more, or infinite scroll) and apply it to ALL list views in the app. Do not mix approaches. | _[to be filled]_ |

---

### UX Standards

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Six required UI components | "You MUST create and use these components. They are NOT optional: 1. Modal.tsx 2. ConfirmModal.tsx 3. Toast.tsx 4. ToastContext.tsx 5. Skeleton.tsx 6. EmptyState.tsx" | Create all six components: `Modal.tsx` (overlay + close + title + content slots), `ConfirmModal.tsx` (destructive action dialog), `Toast.tsx` (success/error/info slide-in), `ToastContext.tsx` (global `showToast(message, type)`), `Skeleton.tsx` (animated placeholder matching content shape), `EmptyState.tsx` (icon + message + CTA button). | _[to be filled]_ |
| 2 | Browser dialogs are banned | "These are strictly forbidden. Using them fails the build: alert(), confirm(), prompt(), console.log for user feedback" | Never use `alert()`, `confirm()`, `prompt()`, or `console.log` for user-facing feedback. Use Toast for messages, ConfirmModal for confirmations, Modal for prompts. | _[to be filled]_ |
| 3 | Text-only empty states are banned | "Text-only empty states ... needs icon + CTA" | Empty states must use the `EmptyState` component with an icon/illustration, descriptive message, AND a call-to-action button. Plain "No items" text is forbidden. | _[to be filled]_ |
| 4 | Loading text is banned | "Loading states that are just the word 'Loading...'" | Never display bare "Loading..." text. Use `Skeleton` components that match the shape of the content being loaded. | _[to be filled]_ |
| 5 | List-Detail-Create-Edit flow | "Any data the user creates/saves MUST follow this pattern: List View ... Detail View ... Create View ... Edit View" | All user data CRUD must implement four distinct views: List (cards/rows + "Create New"), Detail (read-only + Edit/Delete/Share), Create (form, save > Detail), Edit (pre-filled form, save > Detail, cancel > Detail not List). | _[to be filled]_ |
| 6 | No edit-first pattern | "Clicking saved item opens it in edit mode directly ... Using Create form as Edit form ... No way to view an item without editing it ... Single 'smart' component that handles both view and edit" | Items always open in read-only Detail view. Create and Edit are separate views/components. Never combine view+edit into one "smart" component. | _[to be filled]_ |
| 7 | Delete always requires confirmation | "Delete with no confirmation" listed as anti-pattern | Every delete action must go through `ConfirmModal` with explicit user confirmation. No silent deletes. | _[to be filled]_ |
| 8 | Every action needs user feedback | "Success/error with no feedback to user" listed as anti-pattern | Every mutation (create, update, delete) must show either a success or error toast. No silent operations. | _[to be filled]_ |
| 9 | Cancel-edit returns to detail | "Cancel returns to Detail View (not List)" | In Edit view, the Cancel button navigates back to the Detail view of the same item, not to the List view. | _[to be filled]_ |
| 10 | Cancel-create returns to list | "Cancel returns to List View" | In Create view, the Cancel button navigates back to the List view. | _[to be filled]_ |
| 11 | Never show raw timestamps | "Never show raw timestamps. Format dates for humans" | Create a `utils/formatDate.ts` helper. Display: "Just now" (<60s), "Xm ago" (<1h), "Xh ago" (<24h), "Yesterday" (24-48h), "Xd ago" (<7d), "Jan 15" (>7d same year), "Jan 15, 2024" (different year). | _[to be filled]_ |
| 12 | Text truncation is mandatory | "Long text MUST be truncated to prevent layout breaking" | Sidebar items: `truncate max-w-[200px]` (~30 chars). Card descriptions: `line-clamp-2`. Table cells: `truncate max-w-[150px]`. Always pair `truncate` with a `max-w-` value. | _[to be filled]_ |
| 13 | Back navigation on every sub-page | "Every detail/edit page MUST have back navigation" | Detail and Edit pages must have a back button at the top (`mb-6`) using either `navigate(-1)` or an explicit `<Link>` with left arrow icon and "Back" / "Back to [List]" text. | _[to be filled]_ |
| 14 | Five required animations | "Required animations: Modals: Fade in backdrop, scale up content. Toasts: Slide in from top-right. Cards: Subtle lift on hover. Buttons: Slight scale on press. Sidebar: Slide in on mobile" | Implement all five animation types: modal backdrop fade + content scale, toast slide-in from top-right, card hover lift, button press scale, sidebar mobile slide-in. | _[to be filled]_ |
| 15 | Danger zone styling | "mt-12 pt-8 border-t border-red-200 ... text-red-600 ... bg-red-600 hover:bg-red-700" | Account deletion section uses: `mt-12 pt-8` top spacing, `border-t border-red-200` separator, red-600 heading, red-600/700 button. Labeled "Danger Zone". | _[to be filled]_ |
| 16 | Modal overlay pattern | "fixed inset-0 bg-black/50 flex items-center justify-center z-50" | Modals use fixed full-screen overlay with `bg-black/50`, flex centering, `z-50`. Inner content: `bg-surface-base rounded-lg p-6 max-w-md w-full mx-4`. | _[to be filled]_ |
| 17 | Focus states on all interactive elements | "All interactive elements need visible focus ... focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2" | Every button, link, and input must have `focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2`. | _[to be filled]_ |
| 18 | Escape key closes modals | "Modals must handle Escape key" | Every modal must add a `keydown` event listener for `Escape` that calls `onClose()`. Clean up listener on unmount. | _[to be filled]_ |
| 19 | Focus trap in modals | "Focus trap in modals - focus first element, trap Tab key" | Modals must trap keyboard focus: focus the first interactive element on open, cycle Tab within the modal only. | _[to be filled]_ |
| 20 | Icon buttons need aria-label | "Icon-only buttons need aria-label" | Every button containing only an icon (no visible text) must have an `aria-label` attribute describing the action (e.g. "Close modal", "Delete item"). | _[to be filled]_ |
| 21 | Screen reader loading states | "Loading states ... <span className='sr-only'>Loading...</span>" | Add `<span className="sr-only">Loading...</span>` alongside visual loading indicators for screen readers. | _[to be filled]_ |
| 22 | Status updates use aria-live | "<div role='status' aria-live='polite'>{message}</div>" | Dynamic status messages must use `role="status"` and `aria-live="polite"` so screen readers announce changes. | _[to be filled]_ |
| 23 | 404 catch-all route | "<Route path='*' element={<NotFoundPage />} />" | The router must include a `path="*"` catch-all route rendering a `NotFoundPage` component. | _[to be filled]_ |

---

### Mobile/Responsive

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Mobile-first design | "Build mobile-first. Design for mobile, then scale up for larger screens." | Write default (unprefixed) CSS for mobile. Use `sm:` and `lg:` prefixes to add tablet/desktop overrides. | _[to be filled]_ |
| 2 | Three breakpoints | "Mobile: < 640px (default styles, no prefix) ... Tablet: sm:640px and up ... Desktop: lg:1024px and up" | Use Tailwind defaults: mobile (<640px, no prefix), tablet (sm:640px+), desktop (lg:1024px+). | _[to be filled]_ |
| 3 | Sidebar hidden on mobile | "Sidebar hidden by default on mobile ... Hamburger icon in header toggles sidebar" | Sidebar uses `hidden lg:block` (or equivalent). Mobile header has hamburger menu icon to toggle sidebar visibility. | _[to be filled]_ |
| 4 | Sidebar is overlay on mobile | "Sidebar slides in as overlay (not push) ... Clicking outside or nav item closes sidebar ... Add close button inside mobile sidebar" | Mobile sidebar slides over content (not push layout), closes on outside click or nav item click, has a close (X) button inside. | _[to be filled]_ |
| 5 | Cards stack vertically on mobile | "Cards: Full width, stack vertically (mobile) ... Grid 2-3 columns (desktop)" | Card grids: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4`. | _[to be filled]_ |
| 6 | Forms full width on mobile | "Forms: Full width inputs (mobile) ... Max-width container (desktop)" | Form inputs: `w-full lg:max-w-md`. | _[to be filled]_ |
| 7 | Primary buttons full width on mobile | "Buttons: Full width for primary actions (mobile) ... Auto width (desktop)" | Primary action buttons: `w-full lg:w-auto`. | _[to be filled]_ |
| 8 | Modals nearly full screen on mobile | "Modals: Full screen or nearly full (mobile) ... Centered, max-w-md (desktop)" | Modals on mobile should be full-screen or near-full. Desktop: centered with `max-w-md`. | _[to be filled]_ |
| 9 | Minimum 16px text on mobile | "Text: Base size 16px minimum (mobile) ... Can be smaller (desktop)" | Body text must be at least 16px (Tailwind `text-base`) on mobile. Smaller sizes allowed only at `lg:` breakpoint and above. | _[to be filled]_ |
| 10 | 44px minimum touch targets | "Minimum 44px x 44px for all clickable elements on mobile ... Add padding to small icons/buttons to meet minimum ... Adequate spacing between touch targets" | All clickable elements must have a minimum touch area of 44x44px on mobile. Add padding to small icons/buttons. Ensure adequate spacing between adjacent targets. | _[to be filled]_ |
| 11 | Responsive class patterns | "hidden lg:block ... lg:hidden ... w-full lg:max-w-md ... p-4 lg:p-8" | Use `hidden lg:block` for desktop-only, `lg:hidden` for mobile-only, `w-full lg:max-w-md` for responsive width, `p-4 lg:p-8` for responsive padding. | _[to be filled]_ |
| 12 | Layout structure dimensions | "Sidebar: 240px wide, bg-surface-base, border-r ... Header: Full width, bg-surface-base, border-b, h-16 ... Main: flex-1, overflow-y-auto, p-8" | Sidebar: `w-60 bg-surface-base border-r border-border-subtle`. Header: full width, `bg-surface-base border-b h-16`. Main content: `flex-1 overflow-y-auto p-8`. | _[to be filled]_ |
| 13 | Sidebar has bottom help link | "Bottom section: help link (always visible) ... p-4 border-t border-border-subtle" | Sidebar must have a pinned bottom section with `p-4 border-t border-border-subtle` containing a Help & Support link (`mailto:` or equivalent) with a HelpCircle icon. | _[to be filled]_ |
| 14 | Padding scales with breakpoint | "p-4 lg:p-8" | Main content padding: `p-4` on mobile, `p-8` on desktop (lg:). | _[to be filled]_ |

---

### Design System

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Typography scale | "Page Title: 24px Semi-bold ... Section Header: 18px Semi-bold ... Card Title: 16px Medium ... Body Text: 14px Regular ... Small/Meta: 12px Regular" | Page Title: `text-2xl font-semibold text-text-primary`. Section Header: `text-lg font-semibold text-text-primary`. Card Title: `text-base font-medium text-text-primary`. Body: `text-sm text-text-secondary`. Small/Meta: `text-xs text-text-tertiary`. | _[to be filled]_ |
| 2 | Spacing scale | "Card padding: p-6 (24px) ... Section gaps: gap-6 (24px) ... Element gaps: gap-4 (16px)" | Card internal padding: `p-6`. Between sections: `gap-6`. Between elements within a section: `gap-4`. | _[to be filled]_ |
| 3 | Card component class | "bg-surface-base rounded-card border border-border-subtle shadow-card p-6" | Standard card: `bg-surface-base rounded-card border border-border-subtle shadow-card p-6`. | _[to be filled]_ |
| 4 | Primary button class | "bg-brand hover:bg-brand-dark text-text-primary font-medium px-6 py-3 rounded-lg transition-colors" | Primary button: `bg-brand hover:bg-brand-dark text-text-primary font-medium px-6 py-3 rounded-lg transition-colors`. | _[to be filled]_ |
| 5 | Input field class | "bg-surface-muted text-text-primary placeholder:text-text-tertiary px-4 py-3 rounded-lg w-full outline-none focus:ring-2 focus:ring-brand" | Text inputs: `bg-surface-muted text-text-primary placeholder:text-text-tertiary px-4 py-3 rounded-lg w-full outline-none focus:ring-2 focus:ring-brand`. | _[to be filled]_ |
| 6 | Sidebar nav item classes | "space-y-2 ... text-sm text-text-secondary hover:text-text-primary" | Nav links: vertical stack with `space-y-2`, text style `text-sm text-text-secondary hover:text-text-primary`. | _[to be filled]_ |
| 7 | Sidebar recent items section | "mt-6 ... text-xs font-medium text-text-tertiary mb-2" | Sidebar optional items section: `mt-6` spacing, heading `text-xs font-medium text-text-tertiary mb-2`, labeled "Recent Items" or similar. | _[to be filled]_ |
