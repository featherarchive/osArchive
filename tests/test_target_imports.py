from osint_tool.imports.targets import parse_target_lines


def test_parse_target_lines_accepts_colon_and_comma_formats():
    text = """
username: nettihi
domain, example.com
email: test@example.com
"""

    targets = parse_target_lines(text)

    assert [(target.type, target.title) for target in targets] == [
        ("username", "nettihi"),
        ("domain", "example.com"),
        ("email", "test@example.com"),
    ]


def test_parse_target_lines_infers_obvious_plain_values():
    text = """
https://example.com/profile
192.0.2.10
person: Jane Example
example.org
"""

    targets = parse_target_lines(text)

    assert [(target.type, target.title) for target in targets] == [
        ("url", "https://example.com/profile"),
        ("ip", "192.0.2.10"),
        ("person", "Jane Example"),
        ("domain", "example.org"),
    ]


def test_parse_target_lines_reports_invalid_rows():
    result = parse_target_lines("unknown: value\n# comment\n")

    assert result == []
