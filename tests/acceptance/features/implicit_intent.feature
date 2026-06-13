Feature: Implicit intent_id via AGENCY_INTENT environment variable (Spec 018 Win 3)
  Every verb requires an intent_id (the SERVES guard). When one long session serves
  a single intent, repeating the id on every call is ceremony. Win 3: the engine
  falls back to the AGENCY_INTENT env var when no intent_id is supplied. An explicit
  intent_id always wins; with neither, the existing SERVES-guard error still fires
  and names intent_bootstrap.

  Scenario: verb falls back to AGENCY_INTENT env var when no intent_id supplied
    Given a confirmed intent set as AGENCY_INTENT env var
    When I call a verb without supplying an intent_id
    Then the verb succeeds
    And an Invocation SERVES the intent from the env var

  Scenario: explicit intent_id wins over AGENCY_INTENT env var
    Given a confirmed intent set as AGENCY_INTENT env var
    And a second separate confirmed intent
    When I call a verb with the second intent_id explicitly
    Then the Invocation SERVES the second intent

  Scenario: neither intent_id nor AGENCY_INTENT produces the SERVES-guard error
    Given AGENCY_INTENT is not set
    When I invoke a verb against a non-existent intent with no env fallback
    Then a ValueError is raised
    And the error message mentions intent_bootstrap
