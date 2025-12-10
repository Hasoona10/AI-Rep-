"""
Tests for intent classification.
"""
import pytest
from backend.intents import classify_intent, classify_intent_rule_based, Intent


@pytest.mark.asyncio
async def test_greeting_intent():
    """Test greeting intent classification."""
    intent = await classify_intent("Hello, how are you?")
    assert intent in [Intent.GREETING, Intent.GENERAL_QUESTION]


def test_rule_based_hours():
    """Test rule-based hours intent."""
    intent = classify_intent_rule_based("What are your hours?")
    assert intent == Intent.HOURS


def test_rule_based_menu():
    """Test rule-based menu intent."""
    intent = classify_intent_rule_based("What's on the menu?")
    assert intent == Intent.MENU


def test_rule_based_reservation():
    """Test rule-based reservation intent."""
    intent = classify_intent_rule_based("I'd like to make a reservation")
    assert intent == Intent.RESERVATION


if __name__ == "__main__":
    pytest.main([__file__])


