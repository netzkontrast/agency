"""Spec 029 §C — reflect verbs document the closed scope enum.

Closes F4 (Niedrig): the dogfood session failed its first batch_note
because `scope` is a closed enum but neither the verb description nor
the get_schema output named the allowed values."""
from agency.capabilities.reflect import REFLECT_SCOPES, ReflectCapability


def test_reflect_note_docstring_lists_scope_enum():
    doc = ReflectCapability.note.__doc__ or ""
    for scope in REFLECT_SCOPES:
        assert scope in doc, f"scope {scope!r} missing from reflect.note docstring"


def test_reflect_batch_note_docstring_lists_scope_enum():
    doc = ReflectCapability.batch_note.__doc__ or ""
    for scope in REFLECT_SCOPES:
        assert scope in doc, f"scope {scope!r} missing from reflect.batch_note docstring"
