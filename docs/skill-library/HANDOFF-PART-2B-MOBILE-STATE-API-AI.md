# Skill Generation Handoff — Part 2B: Mobile, State, API/Backend, AI/ML (Skills 40-45, 54-61)

> Run `npx ctx7 skills generate`, paste the prompt, save output to the listed path.
> See Part 1A for setup instructions.

---

## MOBILE

### 40. flutter
- **Save to:** `skills/mobile/flutter.md`
- **Library:** Flutter | **Boilerplate:** mobile, dual

**Paste this prompt into ctx7:**
> Flutter development patterns including: StatelessWidget and StatefulWidget fundamentals, state management with Riverpod (providers, StateNotifier, AsyncValue, ref.watch/ref.read), navigation with GoRouter (route configuration, path parameters, guards, redirect), platform channels for native code communication, ThemeData customization for consistent styling, responsive layouts with LayoutBuilder and MediaQuery, and pub.dev package management with pubspec.yaml.

**When the wizard asks:**
- State management? → "Riverpod, not Provider or BLoC"
- Navigation? → "GoRouter, not Navigator 2.0 directly"
- Platforms? → "iOS and Android"

**Must include these patterns:**
- `@riverpod` annotation for code-generated providers
- `ref.watch(provider)` in widgets for reactive updates
- `GoRouter(routes: [GoRoute(path: '/', builder: ...)])` config
- `GoRoute(path: '/user/:id', builder: (context, state) => UserPage(id: state.pathParameters['id']!))`
- `LayoutBuilder(builder: (context, constraints) => ...)` responsive

---

### 41. react-native-expo
- **Save to:** `skills/mobile/react-native-expo.md`
- **Library:** React Native + Expo | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> React Native with Expo patterns including: Expo Router for file-based navigation (app/ directory, layouts, tabs, stacks), EAS Build for app store builds (eas build --platform ios/android), Expo modules for native functionality access, expo-notifications for push notifications setup, app.json and app.config.js configuration, OTA updates with expo-updates, expo-dev-client for custom development builds, and common Expo SDK packages (expo-image, expo-camera, expo-location).

**When the wizard asks:**
- Navigation? → "Expo Router (file-based), not React Navigation directly"
- Builds? → "EAS Build for production"
- Updates? → "expo-updates for OTA"

**Must include these patterns:**
- `app/(tabs)/index.tsx` file-based routing with Expo Router
- `_layout.tsx` for Stack, Tabs, and Drawer navigation layouts
- `eas build --platform ios --profile production`
- `expo-notifications` setup with `registerForPushNotificationsAsync`
- `app.config.js` with dynamic configuration and environment variables

---

## STATE MANAGEMENT

### 42. zustand
- **Save to:** `skills/state/zustand.md`
- **Library:** Zustand | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Zustand state management patterns including: create() for store definition with state and actions, useStore with selectors for preventing unnecessary re-renders, middleware (persist for localStorage/AsyncStorage, immer for immutable updates, devtools for Redux DevTools), TypeScript typing with StateCreator, store slicing for large stores, combining stores, and SSR considerations with Next.js.

**When the wizard asks:**
- Framework? → "React, works with Next.js SSR"
- Middleware? → "persist, immer, devtools"
- TypeScript? → "Full TypeScript with inferred types"

**Must include these patterns:**
- `const useStore = create<State>((set) => ({ count: 0, increment: () => set(s => ({ count: s.count + 1 })) }))`
- Selector: `const count = useStore((state) => state.count)` (prevents re-renders)
- `persist(storeCreator, { name: 'storage-key' })` middleware
- `immer(storeCreator)` for nested state updates
- `devtools(storeCreator, { name: 'MyStore' })` for debugging

---

### 43. tanstack-query
- **Save to:** `skills/state/tanstack-query.md`
- **Library:** TanStack Query (React Query) | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> TanStack Query patterns including: useQuery with queryKey and queryFn for data fetching, useMutation with onSuccess/onError/onSettled callbacks, useInfiniteQuery for pagination with getNextPageParam, optimistic updates via onMutate for instant UI feedback, prefetchQuery for preloading data, queryClient.invalidateQueries for cache invalidation, QueryClientProvider setup, and staleTime/gcTime configuration for cache behavior.

**When the wizard asks:**
- Framework? → "React with Next.js"
- Version? → "TanStack Query v5"
- Caching? → "Include staleTime and gcTime patterns"

**Must include these patterns:**
- `useQuery({ queryKey: ['users'], queryFn: fetchUsers })`
- `useMutation({ mutationFn: createUser, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }) })`
- `useInfiniteQuery` with `getNextPageParam: (lastPage) => lastPage.nextCursor`
- Optimistic: `onMutate: async (newData) => { queryClient.setQueryData(['users'], old => [...old, newData]) }`
- `queryClient.prefetchQuery({ queryKey: ['user', id], queryFn: () => fetchUser(id) })`

---

### 44. jotai
- **Save to:** `skills/state/jotai.md`
- **Library:** Jotai | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Jotai atomic state management patterns including: atom() for primitive state, useAtom/useAtomValue/useSetAtom hooks for reading and writing, derived atoms with get for computed values, async atoms with async get for data fetching, atomWithStorage for localStorage persistence, atomEffect for side effects, Provider component for scoping atoms to subtrees, and atom families with atomFamily for parameterized atoms.

**When the wizard asks:**
- Framework? → "React"
- Persistence? → "atomWithStorage for localStorage"
- Async? → "Async atoms for data fetching"

**Must include these patterns:**
- `const countAtom = atom(0)` primitive atom
- `const [count, setCount] = useAtom(countAtom)` read + write
- `const doubledAtom = atom((get) => get(countAtom) * 2)` derived
- `const userAtom = atom(async (get) => { return await fetchUser(get(idAtom)) })` async
- `const persistedAtom = atomWithStorage('key', defaultValue)` persistence

---

### 45. riverpod
- **Save to:** `skills/state/riverpod.md`
- **Library:** Riverpod (Flutter) | **Boilerplate:** mobile, dual

**Paste this prompt into ctx7:**
> Riverpod state management for Flutter including: Provider types (Provider, StateProvider, NotifierProvider, AsyncNotifierProvider), ref.watch for reactive rebuilds and ref.read for one-time reads, AsyncValue.when() for handling loading/error/data states, .family modifier for parameterized providers, code generation with @riverpod annotation and riverpod_generator, ProviderScope for app-wide state, and testing with ProviderContainer and overrides.

**When the wizard asks:**
- Version? → "Riverpod 2.x with code generation"
- Code gen? → "Yes, @riverpod annotation with build_runner"
- Testing? → "ProviderContainer with overrides"

**Must include these patterns:**
- `@riverpod class UserNotifier extends _$UserNotifier { ... }` code gen
- `ref.watch(userProvider)` in widgets for reactive updates
- `AsyncValue.when(data: (d) => ..., loading: () => ..., error: (e, s) => ...)`
- `.family` modifier: `userProvider(userId)` for parameterized data
- Testing: `container.read(provider)` with `overrides: [provider.overrideWithValue(...)]`

---

## API / BACKEND

### 54. trpc
- **Save to:** `skills/api-backend/trpc.md`
- **Library:** tRPC | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> tRPC patterns including: initTRPC.create() for initialization, router and procedure definitions, publicProcedure with .input(z.object({})).query() and .mutation(), middleware with t.middleware for auth checks, context creation with createContext function, React Query integration with createTRPCReact, error handling with TRPCError and error codes, and subscription procedures with observable for real-time data.

**When the wizard asks:**
- Framework? → "Next.js App Router"
- Validation? → "Zod for input validation"
- Client? → "React Query integration (@trpc/react-query)"

**Must include these patterns:**
- `const t = initTRPC.context<Context>().create()`
- `t.router({ user: t.router({ list: publicProcedure.query(...), create: publicProcedure.input(z.object({...})).mutation(...) }) })`
- `const isAuthed = t.middleware(({ ctx, next }) => { if (!ctx.user) throw new TRPCError({ code: 'UNAUTHORIZED' }); return next({ ctx: { user: ctx.user } }) })`
- `const trpc = createTRPCReact<AppRouter>()` client setup
- `trpc.user.list.useQuery()` and `trpc.user.create.useMutation()` hooks

---

### 55. hono
- **Save to:** `skills/api-backend/hono.md`
- **Library:** Hono | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Hono web framework patterns including: new Hono() app creation, route handlers with app.get/post/put/delete, c.json() and c.text() for responses, middleware with app.use() for logging/CORS/auth, Zod validation with @hono/zod-validator, hono/client for type-safe RPC client generation, adapter patterns for Cloudflare Workers/Node.js/Deno/Bun, and grouped routes with app.route() for modular APIs.

**When the wizard asks:**
- Runtime? → "Cloudflare Workers primary, Node.js secondary"
- Validation? → "@hono/zod-validator"
- Client? → "hono/client for typed RPC"

**Must include these patterns:**
- `const app = new Hono(); app.get('/api/users', (c) => c.json({ users: [] }))`
- `app.post('/api/users', zValidator('json', schema), (c) => { const data = c.req.valid('json'); ... })`
- `app.use('/*', cors(), logger())` middleware chain
- `const client = hc<AppType>('http://localhost:8787')` typed client
- `app.route('/api/v1', apiRoutes)` route grouping

---

### 56. fastapi
- **Save to:** `skills/api-backend/fastapi.md`
- **Library:** FastAPI | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> FastAPI patterns including: app = FastAPI() setup, route decorators @app.get/post/put/delete with path parameters and query parameters, Pydantic BaseModel for request body validation and response models, Depends() for dependency injection (database sessions, auth), middleware with @app.middleware("http"), BackgroundTasks for async work after response, WebSocket routes for real-time communication, and async def handlers for non-blocking I/O.

**When the wizard asks:**
- Python version? → "Python 3.11+"
- ORM? → "SQLAlchemy or raw SQL, show Depends pattern"
- Async? → "async def for all handlers"

**Must include these patterns:**
- `@app.get("/users/{user_id}", response_model=UserResponse)`
- `class CreateUser(BaseModel): name: str; email: EmailStr` Pydantic model
- `async def get_db(): async with SessionLocal() as db: yield db` dependency
- `@app.post("/users", dependencies=[Depends(get_current_user)])` auth
- `background_tasks.add_task(send_email, user.email)` background work

---

### 57. supabase-edge-functions
- **Save to:** `skills/api-backend/supabase-edge-functions.md`
- **Library:** Supabase Edge Functions | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> Supabase Edge Functions patterns including: Deno.serve() for request handling, Deno.env.get() for accessing secrets, CORS headers pattern for browser requests, invoking from client with supabase.functions.invoke(), setting secrets with supabase secrets set, local development with supabase functions serve, deployment with supabase functions deploy, shared code between functions, and error handling with proper HTTP status codes.

**When the wizard asks:**
- Runtime? → "Deno (not Node.js)"
- Use case? → "Webhooks, API proxy, server-side processing"
- Auth? → "Verify JWT from supabase-js client"

**Must include these patterns:**
- `Deno.serve(async (req) => { return new Response(JSON.stringify(data), { headers: corsHeaders }) })`
- `const supabaseClient = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_ANON_KEY')!)`
- `corsHeaders = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type' }`
- Client: `supabase.functions.invoke('function-name', { body: { ... } })`
- `supabase secrets set MY_SECRET=value` for environment variables

---

## AI / ML

### 58. anthropic-sdk
- **Save to:** `skills/ai-ml/anthropic-sdk.md`
- **Library:** Anthropic SDK | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Anthropic Claude SDK patterns including: client.messages.create() for standard completions, model/max_tokens/messages parameters, streaming responses with client.messages.stream() and event handling, tool use (function calling) with tool definitions and tool_result messages, image/vision input with base64 or URL content blocks, system prompt parameter for instructions, and both TypeScript (@anthropic-ai/sdk) and Python (anthropic) SDK usage.

**When the wizard asks:**
- Languages? → "TypeScript primary, Python secondary"
- Features? → "Messages API, streaming, tool use, vision"
- Model? → "claude-sonnet-4-20250514 default, show model parameter"

**Must include these patterns:**
- `const response = await anthropic.messages.create({ model, max_tokens, messages: [{ role: 'user', content: '...' }] })`
- Streaming: `const stream = anthropic.messages.stream({ ... }); for await (const event of stream) { ... }`
- Tool use: `tools: [{ name: 'get_weather', description: '...', input_schema: { type: 'object', properties: { ... } } }]`
- Vision: `content: [{ type: 'image', source: { type: 'base64', media_type: 'image/png', data: '...' } }, { type: 'text', text: '...' }]`
- `system: 'You are a helpful assistant.'` system prompt

---

### 59. openai-sdk
- **Save to:** `skills/ai-ml/openai-sdk.md`
- **Library:** OpenAI SDK | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> OpenAI SDK patterns including: client.chat.completions.create() for chat completions, messages array with system/user/assistant roles, streaming with stream:true and async iteration, function calling with tools parameter and function definitions, embeddings with client.embeddings.create(), Assistants API with threads and runs for stateful conversations, and both TypeScript (openai) and Python (openai) SDK usage.

**When the wizard asks:**
- Languages? → "TypeScript primary, Python secondary"
- Features? → "Chat completions, streaming, function calling, embeddings"
- Model? → "gpt-4o default"

**Must include these patterns:**
- `const response = await openai.chat.completions.create({ model: 'gpt-4o', messages: [...] })`
- Streaming: `const stream = await openai.chat.completions.create({ ..., stream: true }); for await (const chunk of stream) { ... }`
- Function calling: `tools: [{ type: 'function', function: { name: '...', parameters: { ... } } }]`
- Embeddings: `const embedding = await openai.embeddings.create({ model: 'text-embedding-3-small', input: '...' })`
- Assistants: `openai.beta.threads.create()` → `openai.beta.threads.runs.create(threadId, { assistant_id })`

---

### 60. vercel-ai-sdk
- **Save to:** `skills/ai-ml/vercel-ai-sdk.md`
- **Library:** Vercel AI SDK | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> Vercel AI SDK patterns including: streamText() and generateText() for server-side AI calls, useChat() React hook for chat interfaces with streaming, useCompletion() for single-turn completions, tool() function for defining callable tools, provider registry with createOpenAI/createAnthropic for multi-provider support, AI middleware for logging and caching, and React Server Components integration with streamUI() for server-rendered AI responses.

**When the wizard asks:**
- Framework? → "Next.js App Router"
- Providers? → "Anthropic and OpenAI via provider registry"
- UI? → "useChat hook for chat interfaces"

**Must include these patterns:**
- `const result = streamText({ model: anthropic('claude-sonnet-4-20250514'), prompt: '...' })`
- `const { messages, input, handleSubmit } = useChat()` React hook
- `const tools = { weather: tool({ description: '...', parameters: z.object({...}), execute: async (params) => { ... } }) }`
- Provider: `const model = createAnthropic({ apiKey })('claude-sonnet-4-20250514')`
- RSC: `const ui = streamUI({ model, prompt, tools })` server-rendered

---

### 61. langchain
- **Save to:** `skills/ai-ml/langchain.md`
- **Library:** LangChain | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> LangChain patterns including: ChatPromptTemplate for structured prompts, RunnableSequence for composable chains (prompt | model | parser), AgentExecutor with tool definitions for autonomous agents, ConversationBufferMemory for chat history, vector stores with FAISS and Pinecone for semantic search, document loaders for PDF/CSV/web content, StructuredOutputParser for typed responses, and both Python (langchain) and JavaScript (@langchain/core) implementations.

**When the wizard asks:**
- Languages? → "Python primary, JavaScript secondary"
- LLM? → "Works with Anthropic and OpenAI"
- Use case? → "RAG, agents, and chain composition"

**Must include these patterns:**
- `prompt = ChatPromptTemplate.from_messages([("system", "..."), ("human", "{input}")])`
- `chain = prompt | ChatAnthropic(model="claude-sonnet-4-20250514") | StrOutputParser()`
- `agent = create_tool_calling_agent(llm, tools, prompt)` → `AgentExecutor(agent=agent, tools=tools)`
- `vectorstore = FAISS.from_documents(docs, embeddings)` → `retriever = vectorstore.as_retriever()`
- `loader = PyPDFLoader("doc.pdf"); docs = loader.load_and_split()`
