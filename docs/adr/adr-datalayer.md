<!-- agency-node: adr-theme-datalayer -->
---
kind: adr-theme
layer: datalayer
title: "Datalayer — decisions"
scope: "how agency stores, versions and reconciles all state"
status: proposed
last_updated: 2026-06-21
---

# Datalayer — decisions

## keep-both reconciliation — never overwrite, the latest recorded_at wins on read

In the context of a graph-authored and a file-authored version of the same Document diverging, facing edits arriving from both the graph verbs and on-disk markdown at once, we decided for keep-both reconciliation — never overwrite, the latest recorded_at wins on read and neglected last-writer-overwrite, or locking one surface read-only, to achieve no lost edits, full history retained, and files and graph stay peers, accepting that storage grows monotonically and a read must resolve the latest of N revisions rather than read a single row.
_status: proposed_

## a single bi-temporal GraphQLite graph as the one store for every concept

In the context of agency persisting intents, capabilities, lifecycles and memory across sessions, facing the pull to add a purpose-built store (a task table, a doc store, a metrics DB) as each concept arrives, we decided for a single bi-temporal GraphQLite graph as the one store for every concept and neglected per-concept relational tables, an external graph database (Neo4j), a separate document store, to achieve one query surface, one provenance spine, and zero cross-store synchronisation, accepting that graph queries over a SQLite-backed store are less tunable than hand-rolled SQL and a single store is a single blast radius for a corruption bug.
_status: proposed_

## project the hot typed entities (Intent, Agent, Invocation) onto SQLModel tables beside the graph

In the context of typed read-API joins and fulfilment gates being awkward as raw graph traversals, facing the cost of re-deriving typed shapes on every read, we decided for project the hot typed entities (Intent, Agent, Invocation) onto SQLModel tables beside the graph and neglected graph-only with Python-side filtering, or a separate analytics database, to achieve cheap typed joins while the graph stays the source of truth (a projection, not a fork), accepting that the projection must be kept in sync with the graph and adds a second schema to migrate.
_status: proposed_

