Feature: Surface resolution — arg > env > auto fallback (Spec 023)
  resolve_surface() determines which surface form the engine renders.
  Resolution order: explicit arg wins, then AGENCY_SURFACE env var, then
  auto-fallback to "mcp" (the more-capable surface is the safer default).
  Unknown values degrade gracefully; the engine exposes the resolved surface.

  Scenario: explicit arg wins over AGENCY_SURFACE env var
    Given AGENCY_SURFACE env var is set to bash
    When I resolve surface with explicit arg mcp
    Then the resolved surface is mcp

  Scenario: AGENCY_SURFACE env var wins when no arg given
    Given AGENCY_SURFACE env var is set to bash
    When I resolve surface with no arg
    Then the resolved surface is bash

  Scenario: fallback to mcp when neither arg nor env is set
    Given AGENCY_SURFACE is not set
    When I resolve surface with no arg
    Then the resolved surface is mcp

  Scenario: unknown arg raises ValueError
    When I resolve surface with arg websocket
    Then a ValueError is raised

  Scenario: unknown env value falls back silently to mcp
    Given AGENCY_SURFACE env var is set to GIBBERISH
    When I resolve surface with no arg
    Then the resolved surface is mcp

  Scenario: empty string arg is treated as unset and falls back to mcp
    Given AGENCY_SURFACE is not set
    When I resolve surface with an empty string arg
    Then the resolved surface is mcp

  Scenario: engine surface attribute uses the resolver
    Given a fresh agency engine in code-mode
    When I inspect the engine surface attribute
    Then it is a non-empty string from the known surface set
