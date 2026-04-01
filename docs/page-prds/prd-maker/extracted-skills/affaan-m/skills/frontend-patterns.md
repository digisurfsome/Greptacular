# Frontend Development Patterns

**Name**: frontend-patterns
**Description**: Frontend development patterns for React, Next.js, state management, performance optimization, and UI best practices.
**Origin**: ECC

## When to Activate

- Building React components (composition, props, rendering)
- Managing state (useState, useReducer, Zustand, Context)
- Implementing data fetching (SWR, React Query, server components)
- Optimizing performance (memoization, virtualization, code splitting)
- Working with forms (validation, controlled inputs, Zod schemas)
- Handling client-side routing and navigation
- Building accessible, responsive UI patterns

## Component Patterns

### Composition Over Inheritance

Card component with variant prop, CardHeader component, CardBody component. Usage shows composition of smaller pieces.

### Compound Components

```typescript
// Tabs context setup with TypeScript interfaces
// Tabs provider component
// TabList component
// Tab component with active state management
```

### Render Props Pattern

```typescript
// DataLoader generic component with TypeScript
// useEffect for fetching data
// Usage with loading/error states
```

## Custom Hooks Patterns

### useToggle Hook

```typescript
// State management with initial value
// useCallback for toggle function
// Returns tuple with state and function
```

### useQuery Hook

```typescript
// Generic fetching hook with options
// Callback-based success/error handling
// Refetch capability
// enabled conditional fetching
```

### useDebounce Hook

```typescript
// Generic debounce implementation
// setTimeout with cleanup
// Search query example
```

## State Management Patterns

### Context + Reducer Pattern

```typescript
// State interface definition
// Action union type
// Reducer function with switch cases
// Market context creation
// MarketProvider component
// useMarkets custom hook
```

## Performance Optimization

### Memoization

- `useMemo` for expensive computations
- `useCallback` for function stability
- `React.memo` for pure components

### Code Splitting & Lazy Loading

```typescript
// lazy() and Suspense implementation
// HeavyChart lazy component
// ThreeJsBackground lazy component
// Fallback UI patterns
```

### Virtualization for Long Lists

```typescript
// useVirtualizer from @tanstack/react-virtual
// estimateSize property
// overscan optimization
// Dynamic positioning with transform
```

## Form Handling Pattern

### Controlled Form with Validation

```typescript
// FormData interface
// FormErrors interface
// Form state management
// Validation function with rules
// handleSubmit implementation
// Error display
```

## Error Boundary Pattern

```typescript
// Class component structure
// getDerivedStateFromError lifecycle
// componentDidCatch method
// Error UI fallback
// Retry functionality
```

## Animation Patterns

### Framer Motion Animations

```typescript
// AnimatedMarketList with AnimatePresence
// initial, animate, exit properties
// duration transitions
// Modal animations with overlay
```

## Accessibility Patterns

### Keyboard Navigation

```typescript
// Dropdown with key handling
// ArrowDown/ArrowUp management
// Enter key selection
// Escape key handling
// ARIA attributes (role, aria-expanded, aria-haspopup)
```

### Focus Management

```typescript
// Modal focus trap
// previousFocusRef tracking
// Focus restoration on close
// dialog role and aria-modal
```

## Key Takeaway

"Modern frontend patterns enable maintainable, performant user interfaces. Choose patterns that fit your project complexity."
