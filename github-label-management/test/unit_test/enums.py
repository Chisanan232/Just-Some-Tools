import pytest
from github_label_bot.enums import Operation


class TestOperation:

    @pytest.mark.parametrize(
        "input_value, expected_output",
        [
            ("sync_upstream", Operation.Sync_UpStream),
            ("sync_download", Operation.Sync_Download),
        ],
    )
    def test_to_enum_valid_cases(self, input_value, expected_output):
        assert Operation.to_enum(input_value) == expected_output

    @pytest.mark.parametrize(
        "input_value, expected_exception, match",
        [
            ("INVALID", ValueError, r"invalid Operation"),
            ("", ValueError, r"invalid Operation"),
            (None, ValueError, r"invalid Operation"),
        ],
    )
    def test_to_enum_invalid_cases(self, input_value, expected_exception, match):
        with pytest.raises(expected_exception, match=match):
            Operation.to_enum(input_value)
