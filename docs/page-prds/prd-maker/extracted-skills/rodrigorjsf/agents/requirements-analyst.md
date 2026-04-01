# Requirements-Analyst Agent

This agent transforms unstructured product context into engineer-ready specifications using two distinct modes.

## Core Function

The requirements-analyst specializes in converting "raw context into precise, unambiguous specifications" with expertise in domain-driven design and regulated-domain software architecture.

## Operating Modes

**Full Mode** — Generates initial PRDs by producing:
- Functional Requirements (RF-XXX): Actor-action-outcome format with acceptance criteria
- Non-Functional Requirements (RNF): Performance, scalability, security, availability, observability, compliance
- Domain Rules (DR-XXX): Invariants, state machines, validation rules
- Ubiquitous Language: Domain glossary with definitions and synonym flags
- Compliance Mapping: Regulation-to-technical requirements with affected features/entities

**Delta Mode** — Analyzes scope changes for /prd-evolve by:
- Classifying change types (new feature, domain rule, technology, compliance, integration, scope shift, removal, architecture pivot)
- Mapping to affected artifacts using an impact table
- Determining version bumps (MAJOR, MINOR, PATCH)
- Identifying pending research topics
- Highlighting unaffected artifacts

## Key Deliverables

Output includes structured JSON with sequential IDs, phase assignments (MVP/POST-MVP), testable acceptance criteria, domain entity mappings, and regulatory traceability with ref_ids. The agent also catalogs out-of-scope items and clarifications needed.
