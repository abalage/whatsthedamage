import pytest
from whatsthedamage.utils.date_converter import DateConverter


def test_convert_to_epoch_valid_date():
    date_str = "2023.10.05"
    date_format = "%Y.%m.%d"
    expected_epoch = 1696464000  # This value should be checked for correctness
    assert DateConverter.convert_to_epoch(date_str, date_format) == expected_epoch


def test_convert_to_epoch_invalid_date():
    date_str = "invalid_date"
    date_format = "%Y.%m.%d"
    with pytest.raises(ValueError):
        DateConverter.convert_to_epoch(date_str, date_format)


def test_convert_from_epoch_valid_epoch():
    epoch = 1696464000
    date_format = "%Y.%m.%d"
    expected_date_str = "2023.10.05"
    assert DateConverter.convert_from_epoch(epoch, date_format) == expected_date_str


def test_convert_from_epoch_invalid_epoch():
    # AD 1 is before the epoch
    epoch = -62194560000
    date_format = "%Y.%m.%d"
    with pytest.raises(ValueError):
        DateConverter.convert_from_epoch(epoch, date_format)


def test_convert_month_number_to_name_valid():
    assert DateConverter.convert_month_number_to_name(1) == "January"
    assert DateConverter.convert_month_number_to_name(12) == "December"


def test_convert_month_number_to_name_invalid():
    with pytest.raises(ValueError):
        DateConverter.convert_month_number_to_name(0)
    with pytest.raises(ValueError):
        DateConverter.convert_month_number_to_name(13)
