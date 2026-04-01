# The Twelve-Factor App

> A methodology for building software-as-a-service apps.
>
> Source: https://12factor.net/

---

## Introduction

The Twelve-Factor App is a methodology for building software-as-a-service apps designed to address modern development challenges. Applications following this approach should:

- Utilize **declarative setup formats** to streamline developer onboarding
- Maintain **clean OS contracts** for maximum portability across environments
- Deploy readily on **cloud platforms** without dedicated server infrastructure
- **Minimize gaps** between development and production settings
- **Scale efficiently** without major architectural changes

The methodology applies universally across programming languages and backing service combinations.

## Background

This framework emerged from extensive experience at Heroku, synthesizing insights from hundreds of deployed applications. The creators developed these principles to address systemic problems in modern development, establish shared vocabulary for discussing challenges, and propose conceptual solutions -- inspired by enterprise architecture patterns literature.

## Target Audience

The document serves developers building service-based applications and operations engineers managing their deployment and operations.

---

## I. Codebase

**One codebase tracked in revision control, many deploys**

A twelve-factor application maintains a single codebase under version control (Git, Mercurial, or Subversion) that maps to multiple deployment instances.

### Single Codebase Per App

- Each app has exactly one codebase, though it may consist of multiple repositories sharing a root commit in decentralized systems.
- Multiple codebases indicate a distributed system, not a single app.
- Shared code should be extracted into libraries managed through dependency managers.

### Multiple Deploys from One Codebase

- A "deploy" represents any running instance -- production, staging, or local development environments.
- The same codebase exists across all deploys, though different code versions may be active in each.
- Example: developers may have uncommitted changes, staging may have undeployed commits, yet all reference the identical codebase.

---

## II. Dependencies

**Explicitly declare and isolate dependencies**

A twelve-factor application must follow two essential practices:

1. **Dependency Declaration**: Applications should never assume system-wide packages exist. Instead, they must comprehensively and precisely specify all dependencies through a manifest file.

2. **Dependency Isolation**: During execution, a dedicated tool ensures that implicit dependencies don't infiltrate from the surrounding system environment.

### Practical Benefits

The methodology simplifies developer onboarding considerably. New team members can clone the codebase and run a deterministic build command (like `bundle install` for Ruby) after installing only the language runtime and dependency manager. This eliminates setup ambiguity.

### System Tools Consideration

Applications should not assume system tools (ImageMagick, curl) will be available across all deployment environments. If required, such tools should be packaged directly within the application rather than relying on external availability.

### Implementation Examples

Different languages employ varying toolchains:

- **Ruby**: Bundler with Gemfile and `bundle exec`
- **Python**: Pip for declaration, Virtualenv for isolation
- **Clojure**: Leiningen dependency management
- **C**: Autoconf with static linking

**Critical principle**: Both declaration and isolation must work together -- using only one approach is insufficient.

---

## III. Config

**Store config in the environment**

### What Constitutes Configuration

Configuration encompasses everything that varies across different deployment environments (staging, production, development). This includes:

- Database and service connections (Memcached, etc.)
- External service credentials (Amazon S3, Twitter)
- Per-deployment values like hostnames

### The Problem with Traditional Approaches

The methodology explicitly rejects storing configuration as code constants, which violates the principle of strict separation of config from code. Config files not tracked in version control present risks -- files may be accidentally committed, scattered across locations in inconsistent formats, and often use language-specific approaches.

### The Recommended Solution

The twelve-factor app stores config in **environment variables** rather than constants or external files. Environment variables offer distinct advantages:

- Simple to modify between deployments without code changes
- Minimal risk of accidental repository commits
- Language and operating system agnostic standards

### Scaling Configuration Management

The methodology warns against grouping variables into named "environments" (development, test, production). This approach becomes brittle as projects expand. Instead, the twelve-factor approach treats each environment variable as an independent, granular control -- never grouped together as "environments," but instead independently managed for each deploy.

This design scales smoothly as applications naturally expand across multiple deployments throughout their lifecycle.

---

## IV. Backing Services

**Treat backing services as attached resources**

A backing service is any service an application consumes over the network during normal operations. These are treated as attached resources rather than integral components.

### Examples of Backing Services

**Locally-managed services:**
- Datastores (MySQL, CouchDB)
- Messaging/queueing systems (RabbitMQ, Beanstalkd)
- SMTP services (Postfix)
- Caching systems (Memcached)

**Third-party services:**
- SMTP providers (Postmark)
- Metrics services (New Relic, Loggly)
- Asset services (Amazon S3)
- API services (Twitter, Google Maps, Last.fm)

### Key Principle

The code for a twelve-factor app makes no distinction between local and third-party services. Both types are accessed via URLs or credentials stored in configuration, enabling seamless swaps without code modifications.

### Resource Management

Each distinct backing service counts as a separate resource. For example, two MySQL databases for sharding represent two resources. These resources can be attached and detached dynamically -- administrators can replace a malfunctioning database with a restored backup without any code changes.

---

## V. Build, Release, Run

**Strictly separate build and run stages**

### The Three Stages

**Build Stage**: Transforms code repository into an executable bundle. It fetches vendor dependencies and compiles binaries and assets using a specific code commit.

**Release Stage**: Combines the build with deployment configuration, creating a ready-to-execute release containing both components.

**Run Stage**: Executes the app in the production environment by launching processes against a selected release.

### Key Principles

It is impossible to make changes to the code at runtime, since there is no way to propagate those changes back to the build stage.

Every release requires a unique identifier -- either a timestamp or incrementing number -- and functions as an append-only ledger. Releases cannot be modified; changes mandate new releases.

### Operational Implications

Build initiation occurs through developer action, while runtime execution can happen automatically during server reboots or process restarts. This distinction means the run stage should minimize complexity to prevent failures during off-hours when developers are unavailable, whereas the build stage can be more intricate since errors remain visible to deploying developers.

---

## VI. Processes

**Execute the app as one or more stateless processes**

The Twelve-Factor App methodology dictates that applications should run as stateless and share-nothing processes. Any persistent data must be stored in external backing services, typically databases, rather than in the process itself.

### Stateless Architecture

The memory space or filesystem of the process can be used as a brief, single-transaction cache, but developers should never assume cached data will persist across requests or restarts.

### Process Distribution

With multiple process instances running concurrently, subsequent requests will likely be handled by different processes. Even single-process deployments face state loss during restarts due to code deployments or infrastructure changes.

### Asset Handling

Compilation and asset packaging should occur during the build stage rather than at runtime, using tools like the Rails asset pipeline configured appropriately.

### Session Management

The methodology explicitly prohibits "sticky sessions" that cache user data in process memory. Instead, applications should use external datastores like Memcached or Redis that support time-based expiration for session information.

---

## VII. Port Binding

**Export services via port binding**

The twelve-factor app methodology emphasizes that applications should be entirely self-contained. Rather than depending on a webserver container injected at runtime, apps should export HTTP as a service by binding to a port and listening for incoming requests.

### Self-Containment

Apps don't rely on external webserver injection. Instead, they include necessary webserver libraries in their own codebase through dependency declaration.

### How It Works

During local development, developers access services via URLs like `http://localhost:5000/`. In production, a routing layer directs public-facing requests to the port-bound processes.

### Implementation Examples

Different languages use different libraries:

- **Python**: Tornado
- **Ruby**: Thin
- **Java/JVM**: Jetty

### Broader Applications

Port binding extends beyond HTTP. Any server software can operate this way, including:

- **ejabberd** (XMPP protocol)
- **Redis** (Redis protocol)

### Additional Benefit

The port-binding approach enables service composition -- one app can serve as a backing service for another by sharing its URL through configuration.

---

## VIII. Concurrency

**Scale out via the process model**

Processes are a first-class citizen in twelve-factor applications. This factor emphasizes treating processes as primary architectural components rather than implementation details hidden from developers.

### Key Principles

The methodology draws inspiration from Unix service daemon models, allowing developers to assign different workload types to specific process categories. HTTP requests might be handled by web processes while background tasks run on worker processes.

### Internal vs. External Scaling

While individual processes can manage their own concurrency through threading or event-driven models (EventMachine, Twisted, Node.js), applications must ultimately scale horizontally across multiple machines rather than relying solely on vertical growth within a single VM.

### Process Formation

The collection of process types and their quantities is called the **process formation**. The share-nothing architecture enables straightforward horizontal scaling without complex coordination.

### Operational Practices

Applications should avoid daemonizing or creating PID files. Instead, rely on external process managers like systemd, cloud platform tools, or development utilities like Foreman to handle output streams, manage crashes, and coordinate restarts and shutdowns.

---

## IX. Disposability

**Maximize robustness with fast startup and graceful shutdown**

Processes can be started or stopped at a moment's notice. This design principle enables rapid scaling, quick deployments, and improved system resilience.

### Fast Startup

Applications should minimize startup time, ideally reaching readiness within seconds. This agility benefits both deployment processes and scaling operations, while allowing process managers to migrate services to new infrastructure more efficiently.

### Graceful Shutdown

Processes should respond to SIGTERM signals by ceasing to accept new requests, completing existing work, then exiting cleanly.

- **For web services**: Stop port listeners while allowing current HTTP requests to complete (assuming requests remain short-lived).
- **For worker processes**: Jobs should return to queues upon shutdown. Examples include RabbitMQ's NACK mechanism and automatic Beanstalkd job returns. Lock-based systems like Delayed Job must explicitly release locks.

### Robustness Against Sudden Failure

Though less frequent than graceful shutdowns, unexpected hardware failures occur. The methodology recommends robust queueing backends like Beanstalkd that automatically requeue jobs when workers disconnect.

Twelve-factor applications should handle non-graceful terminations, with **crash-only design** representing this concept taken to its logical conclusion.

---

## X. Dev/Prod Parity

**Keep development, staging, and production as similar as possible**

### The Problem

Historically, substantial gaps existed between development environments (where developers make live edits locally) and production (where end users access the app). These manifest in three areas:

- **Time gap**: Code may take days, weeks, or months to reach production.
- **Personnel gap**: Different people write code versus deploy it.
- **Tools gap**: Dev stacks (Nginx, SQLite, OS X) differ from production (Apache, MySQL, Linux).

### The Twelve-Factor Solution

The twelve-factor app is designed for continuous deployment by keeping the gap between development and production small. This involves:

- Reducing deployment time to hours or minutes.
- Having code authors involved in deployment and production monitoring.
- Maintaining nearly identical development and production environments.

### Backing Services

A critical area for dev/prod parity involves databases, queues, and caches. The methodology cautions against using lightweight services locally while deploying robust versions in production (e.g., SQLite vs. PostgreSQL).

**Key principle**: The twelve-factor developer resists the urge to use different backing services between development and production, as incompatibilities between services cause code to fail in production despite passing tests elsewhere.

### Modern Solutions

Modern tools make environment parity achievable: package managers (Homebrew, apt-get), provisioning tools (Chef, Puppet), and containerization (Docker, Vagrant) enable developers to locally replicate production environments at minimal cost.

---

## XI. Logs

**Treat logs as event streams**

Logs provide visibility into the behavior of a running app. Rather than managing log files directly, applications should output event streams to standard output, allowing the execution environment to handle routing and storage.

### What Apps Should Do

- Write event streams unbuffered to `stdout`.
- Never manage logfiles or attempt to route output.
- Allow each running process to emit its own event stream.

### Development vs. Production

- During **local development**, developers observe the stream in their terminal.
- In **staging/production**, the execution environment captures and collates all streams, routing them to archival destinations.

### Benefits of This Approach

The event stream can be directed toward various systems for analysis:

- Real-time terminal monitoring
- Log indexing systems like Splunk
- Data warehousing solutions such as Hadoop/Hive

These systems enable:

- Finding specific events in the past
- Trend analysis and graphing
- Automated alerting based on custom thresholds

### Implementation Tools

Open-source solutions like Logplex and Fluentd facilitate log routing and management.

---

## XII. Admin Processes

**Run admin/management tasks as one-off processes**

The Twelve-Factor App distinguishes between regular long-running processes and separate administrative tasks. Admin processes handle occasional maintenance activities that developers need to perform on applications.

### Common Admin Tasks

- Database migrations (e.g., `manage.py migrate` in Django, `rake db:migrate` in Rails)
- Interactive shells/REPLs for inspecting models and executing arbitrary code
- One-time scripts stored in the application repository

### Key Requirements

**Identical Environment**: Admin processes must run in the same environment as standard application processes, using the same codebase, configuration, and release version.

**Dependency Management**: The same isolation techniques applied to web processes should extend to administrative tasks. For instance, Ruby applications using `bundle exec thin start` should run migrations with `bundle exec rake db:migrate`. Python applications leveraging Virtualenv should use the vendored Python binary consistently.

**Code Shipping**: Administrative code must be included with application code to prevent synchronization issues between deployment versions.

### Execution Models

- **Local deployment**: Developers invoke one-off processes directly via shell commands.
- **Production deployment**: Remote execution mechanisms like SSH enable administrators to run processes.

The methodology favors programming languages with built-in REPL capabilities and straightforward script execution patterns.

---

## Quick Reference

| # | Factor | Key Phrase |
|---|--------|-----------|
| I | Codebase | One codebase tracked in revision control, many deploys |
| II | Dependencies | Explicitly declare and isolate dependencies |
| III | Config | Store config in the environment |
| IV | Backing Services | Treat backing services as attached resources |
| V | Build, Release, Run | Strictly separate build and run stages |
| VI | Processes | Execute the app as one or more stateless processes |
| VII | Port Binding | Export services via port binding |
| VIII | Concurrency | Scale out via the process model |
| IX | Disposability | Maximize robustness with fast startup and graceful shutdown |
| X | Dev/Prod Parity | Keep development, staging, and production as similar as possible |
| XI | Logs | Treat logs as event streams |
| XII | Admin Processes | Run admin/management tasks as one-off processes |
