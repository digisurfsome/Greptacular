# Hexagonal Architecture (Ports & Adapters)

**Name**: hexagonal-architecture
**Origin**: ECC
**Description**: Design, implement, and refactor Ports & Adapters systems with clear domain boundaries, dependency inversion, and testable use-case orchestration.

## Core Definition

Hexagonal architecture maintains business logic independently from frameworks, transport mechanisms, and persistence implementations. The application's core relies on abstract ports, with adapters fulfilling those contracts at system boundaries.

## When to Use

- Building features prioritizing maintainability and testability
- Refactoring layered or framework-dependent code mixing domain and I/O logic
- Supporting multiple interfaces for identical use cases (HTTP, CLI, workers, scheduled jobs)
- Replacing infrastructure without rewriting business rules

**Activation signals:** Requests involving boundaries, domain-centric design, decoupling tightly coupled services, or isolating application logic from specific libraries.

## Core Concepts

- **Domain Model**: Business rules and entities/value objects without framework imports
- **Use Cases (Application Layer)**: Orchestrate domain behavior and workflow steps
- **Inbound Ports**: Contracts describing what the application can do (commands/queries/use-case interfaces)
- **Outbound Ports**: Contracts for dependencies the application needs (repositories, gateways, event publishers, clock, UUID, etc.)
- **Adapters**: Infrastructure and delivery implementations at system edges (HTTP controllers, database repositories, queue consumers, SDK wrappers)
- **Composition Root**: Single location binding concrete adapters to use cases

**Dependency Direction Principle:**
- Adapters -> application/domain
- Application -> port interfaces
- Domain -> domain-only abstractions
- Domain -> no external dependencies

## Six-Step Implementation Process

### Step 1: Model a Use Case Boundary
Define a single use case with explicit input and output DTO. Exclude transport specifics (Express `req`, GraphQL `context`, job wrappers).

### Step 2: Define Outbound Ports First
Identify all side effects as ports:
- Persistence (`UserRepositoryPort`)
- External calls (`BillingGatewayPort`)
- Cross-cutting concerns (`LoggerPort`, `ClockPort`)

Ports model capabilities, not technologies.

### Step 3: Implement Use Case with Pure Orchestration
Use case receives ports via constructor/arguments. Validates application invariants, coordinates domain rules, returns plain data structures.

### Step 4: Build Adapters at the Edge
- Inbound: converts protocol input to use-case input
- Outbound: maps application contracts to concrete APIs/ORM/query builders
- Mapping remains in adapters, not inside use cases

### Step 5: Wire Everything in Composition Root
Instantiate adapters, inject into use cases. Centralize wiring to avoid hidden service-locator patterns.

### Step 6: Test Per Boundary
- Unit test use cases with fake ports
- Integration test adapters with real infrastructure
- End-to-end test user-facing flows through inbound adapters

## Architecture Diagram

```
Client (HTTP/CLI/Worker)
  -> Inbound Adapter
    -> UseCase (Application Layer)
      -> OutboundPort (Interface)
        <- Outbound Adapter
          -> DB/API/Queue
      -> DomainModel
```

## Suggested Module Layout (Feature-First)

```
src/
  features/
    orders/
      domain/
        Order.ts
        OrderPolicy.ts
      application/
        ports/
          inbound/
            CreateOrder.ts
          outbound/
            OrderRepositoryPort.ts
            PaymentGatewayPort.ts
        use-cases/
          CreateOrderUseCase.ts
      adapters/
        inbound/
          http/
            createOrderRoute.ts
        outbound/
          postgres/
            PostgresOrderRepository.ts
          stripe/
            StripePaymentGateway.ts
      composition/
        ordersContainer.ts
```

## TypeScript Implementation Examples

### Port Interface Definitions

```typescript
export interface OrderRepositoryPort {
  save(order: Order): Promise<void>;
  findById(orderId: string): Promise<Order | null>;
}

export interface PaymentGatewayPort {
  authorize(input: { orderId: string; amountCents: number }): Promise<{ authorizationId: string }>;
}
```

### Use Case Implementation

```typescript
type CreateOrderInput = {
  orderId: string;
  amountCents: number;
};

type CreateOrderOutput = {
  orderId: string;
  authorizationId: string;
};

export class CreateOrderUseCase {
  constructor(
    private readonly orderRepository: OrderRepositoryPort,
    private readonly paymentGateway: PaymentGatewayPort
  ) {}

  async execute(input: CreateOrderInput): Promise<CreateOrderOutput> {
    const order = Order.create({ id: input.orderId, amountCents: input.amountCents });

    const auth = await this.paymentGateway.authorize({
      orderId: order.id,
      amountCents: order.amountCents,
    });

    // markAuthorized returns a new Order instance; it does not mutate in place
    const authorizedOrder = order.markAuthorized(auth.authorizationId);
    await this.orderRepository.save(authorizedOrder);

    return {
      orderId: order.id,
      authorizationId: auth.authorizationId,
    };
  }
}
```

### Outbound Adapter Implementation

```typescript
export class PostgresOrderRepository implements OrderRepositoryPort {
  constructor(private readonly db: SqlClient) {}

  async save(order: Order): Promise<void> {
    await this.db.query(
      "insert into orders (id, amount_cents, status, authorization_id) values ($1, $2, $3, $4)",
      [order.id, order.amountCents, order.status, order.authorizationId]
    );
  }

  async findById(orderId: string): Promise<Order | null> {
    const row = await this.db.oneOrNone("select * from orders where id = $1", [orderId]);
    return row ? Order.rehydrate(row) : null;
  }
}
```

### Composition Root

```typescript
export const buildCreateOrderUseCase = (deps: { db: SqlClient; stripe: StripeClient }) => {
  const orderRepository = new PostgresOrderRepository(deps.db);
  const paymentGateway = new StripePaymentGateway(deps.stripe);

  return new CreateOrderUseCase(orderRepository, paymentGateway);
};
```

## Multi-Language Implementation

### TypeScript/JavaScript
- Ports: `application/ports/*` as interfaces/types
- Use cases: classes/functions with constructor/argument injection
- Adapters: `adapters/inbound/*`, `adapters/outbound/*`
- Composition: explicit factory/container module (no hidden globals)

### Java
- Packages: `domain`, `application.port.in`, `application.port.out`, `application.usecase`, `adapter.in`, `adapter.out`
- Ports: interfaces in `application.port.*`
- Use cases: plain classes (Spring `@Service` optional, not required)
- Composition: Spring config or manual wiring class

### Kotlin
- Modules/packages mirror Java split
- Ports: Kotlin interfaces
- Use cases: classes with constructor injection (Koin/Dagger/Spring/manual)
- Composition: module definitions or dedicated composition functions

### Go
- Packages: `internal/<feature>/domain`, `application`, `ports`, `adapters/inbound`, `adapters/outbound`
- Ports: small interfaces owned by consuming application package
- Use cases: structs with interface fields plus explicit `New...` constructors
- Composition: wire in `cmd/<app>/main.go` or dedicated wiring package

## Anti-Patterns to Avoid

- Domain entities importing ORM models, web framework types, or SDK clients
- Use cases reading directly from `req`, `res`, or queue metadata
- Returning database rows directly without domain/application mapping
- Adapters calling each other instead of flowing through use-case ports
- Spreading dependency wiring across files with hidden global singletons

## Migration Playbook

### Sequential Migration Approach
1. Select one vertical slice (single endpoint/job) with frequent change pain
2. Extract use-case boundary with explicit input/output types
3. Introduce outbound ports around existing infrastructure calls
4. Move orchestration logic from controllers/services into use case
5. Keep old adapters; delegate to new use case
6. Add tests around new boundary (unit + adapter integration)
7. Repeat slice-by-slice; avoid full rewrites

### Refactoring Strategies
- **Strangler approach:** keep current endpoints, route one use case at a time through new ports/adapters
- **Avoid big-bang rewrites:** migrate per feature slice with characterization tests
- **Facade first:** wrap legacy services behind outbound ports before replacing internals
- **Composition freeze:** centralize wiring early to prevent dependency leaks
- **Slice selection rule:** prioritize high-churn, low-blast-radius flows
- **Rollback path:** maintain reversible toggle or route switch per migrated slice

## Testing Guidance

- **Domain Tests**: Test entities/value objects as pure business rules without mocks or framework setup
- **Use-Case Unit Tests**: Test orchestration with fakes/stubs for outbound ports; assert business outcomes and port interactions
- **Outbound Adapter Contract Tests**: Define shared contract suites at port level; run against each implementation
- **Inbound Adapter Tests**: Verify protocol mapping (HTTP/CLI/queue payload to use-case input and response/error mapping)
- **Adapter Integration Tests**: Run against real infrastructure (DB/API/queue) for serialization, schema/query behavior, retries, timeouts
- **End-to-End Tests**: Cover critical user journeys through inbound adapter -> use case -> outbound adapter
- **Refactor Safety**: Add characterization tests before extraction; retain until new boundary behavior is stable

## Best Practices Checklist

- [ ] Domain and use-case layers import only internal types and ports
- [ ] Every external dependency represented by outbound port
- [ ] Validation occurs at boundaries (inbound adapter + use-case invariants)
- [ ] Use immutable transformations (return new values/entities, not mutations)
- [ ] Errors translated across boundaries (infrastructure errors -> application/domain errors)
- [ ] Composition root explicit and auditable
- [ ] Use cases testable with simple in-memory fakes
- [ ] Refactoring starts from one vertical slice with behavior-preserving tests
- [ ] Language/framework specifics stay in adapters, never in domain rules
