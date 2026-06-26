"""
Comprehensive tests for utils modules, system routes, and main routes.
Coverage targets: validators.py, price_calculator.py, helpers.py, routes/system.py, routes/main.py
"""
import pytest
from datetime import date, datetime
from unittest.mock import patch, MagicMock

from utils.validators import (
  validate_locomotive_number,
  validate_decoder_number,
  validate_trainset_number,
  validate_car_number,
  validate_field,
  VALIDATION_RULES
)
from utils.price_calculator import SafeEval, calculate_price
from utils.helpers import (
  parse_purchase_date,
  safe_int,
  safe_float,
  validate_unique,
  api_success,
  api_error,
  parse_boolean,
  generate_brand_abbreviation
)
from models import (
  db, Brand, Depot, Merchant, PowerType,
  LocomotiveSeries, LocomotiveModel, CarriageSeries, CarriageModel,
  TrainsetSeries, TrainsetModel, ChipInterface, ChipModel,
  Locomotive, CarriageSet, Trainset, LocomotiveHead
)


# ============================================================
# validators.py tests
# ============================================================

class TestValidateLocomotiveNumber:
  """Tests for validate_locomotive_number: 4-12 digits, leading zeros OK."""

  def test_valid_min_length(self):
    assert validate_locomotive_number('1234') is True

  def test_valid_max_length(self):
    assert validate_locomotive_number('123456789012') is True

  def test_valid_with_leading_zeros(self):
    assert validate_locomotive_number('0001') is True

  def test_valid_all_zeros(self):
    assert validate_locomotive_number('0000') is True

  def test_valid_mid_length(self):
    assert validate_locomotive_number('123456') is True

  def test_invalid_too_short(self):
    assert validate_locomotive_number('123') is False

  def test_invalid_too_long(self):
    assert validate_locomotive_number('1234567890123') is False

  def test_invalid_empty(self):
    assert validate_locomotive_number('') is False

  def test_invalid_none(self):
    assert validate_locomotive_number(None) is False

  def test_invalid_letters(self):
    assert validate_locomotive_number('abcd') is False

  def test_invalid_special_chars(self):
    assert validate_locomotive_number('1234-') is False

  def test_invalid_spaces(self):
    assert validate_locomotive_number('12 34') is False

  def test_invalid_decimal(self):
    assert validate_locomotive_number('12.34') is False


class TestValidateDecoderNumber:
  """Tests for validate_decoder_number: 1-4 digits, no leading zero."""

  def test_valid_single_digit(self):
    assert validate_decoder_number('1') is True

  def test_valid_max_length(self):
    assert validate_decoder_number('9999') is True

  def test_valid_two_digits(self):
    assert validate_decoder_number('42') is True

  def test_valid_three_digits(self):
    assert validate_decoder_number('123') is True

  def test_invalid_leading_zero(self):
    assert validate_decoder_number('01') is False

  def test_invalid_zero_alone(self):
    assert validate_decoder_number('0') is False

  def test_invalid_too_long(self):
    assert validate_decoder_number('10000') is False

  def test_invalid_empty(self):
    assert validate_decoder_number('') is False

  def test_invalid_none(self):
    assert validate_decoder_number(None) is False

  def test_invalid_letters(self):
    assert validate_decoder_number('ab') is False

  def test_invalid_special_chars(self):
    assert validate_decoder_number('1-2') is False

  def test_invalid_spaces(self):
    assert validate_decoder_number('1 2') is False


class TestValidateTrainsetNumber:
  """Tests for validate_trainset_number: 3-12 digits, leading zeros OK."""

  def test_valid_min_length(self):
    assert validate_trainset_number('123') is True

  def test_valid_max_length(self):
    assert validate_trainset_number('123456789012') is True

  def test_valid_with_leading_zeros(self):
    assert validate_trainset_number('001') is True

  def test_valid_mid_length(self):
    assert validate_trainset_number('12345') is True

  def test_invalid_too_short(self):
    assert validate_trainset_number('12') is False

  def test_invalid_too_long(self):
    assert validate_trainset_number('1234567890123') is False

  def test_invalid_empty(self):
    assert validate_trainset_number('') is False

  def test_invalid_none(self):
    assert validate_trainset_number(None) is False

  def test_invalid_letters(self):
    assert validate_trainset_number('abc') is False

  def test_invalid_special_chars(self):
    assert validate_trainset_number('12-3') is False


class TestValidateCarNumber:
  """Tests for validate_car_number: 1-20 alphanumeric/hyphen."""

  def test_valid_single_digit(self):
    assert validate_car_number('1') is True

  def test_valid_single_letter(self):
    assert validate_car_number('A') is True

  def test_valid_max_length(self):
    assert validate_car_number('A' * 20) is True

  def test_valid_alphanumeric(self):
    assert validate_car_number('ABC123') is True

  def test_valid_with_hyphen(self):
    assert validate_car_number('ABC-123') is True

  def test_valid_all_hyphens(self):
    assert validate_car_number('---') is True

  def test_valid_mixed_case(self):
    assert validate_car_number('AbC123-XyZ') is True

  def test_invalid_too_long(self):
    assert validate_car_number('A' * 21) is False

  def test_invalid_empty(self):
    assert validate_car_number('') is False

  def test_invalid_none(self):
    assert validate_car_number(None) is False

  def test_invalid_special_chars(self):
    assert validate_car_number('ABC_123') is False

  def test_invalid_spaces(self):
    assert validate_car_number('ABC 123') is False

  def test_invalid_unicode(self):
    assert validate_car_number('中文') is False


class TestValidationRules:
  """Tests for VALIDATION_RULES constant dict."""

  def test_all_expected_keys_present(self):
    expected = {'locomotive_number', 'decoder_number', 'trainset_number', 'car_number'}
    assert set(VALIDATION_RULES.keys()) == expected

  def test_each_rule_has_required_fields(self):
    for ruleName, rule in VALIDATION_RULES.items():
      assert 'pattern' in rule, f"Missing 'pattern' in {ruleName}"
      assert 'message' in rule, f"Missing 'message' in {ruleName}"
      assert 'min_length' in rule, f"Missing 'min_length' in {ruleName}"
      assert 'max_length' in rule, f"Missing 'max_length' in {ruleName}"

  def test_locomotive_number_pattern(self):
    import re
    pattern = VALIDATION_RULES['locomotive_number']['pattern']
    assert re.match(pattern, '0001')
    assert re.match(pattern, '123456789012')
    assert not re.match(pattern, '123')

  def test_decoder_number_pattern(self):
    import re
    pattern = VALIDATION_RULES['decoder_number']['pattern']
    assert re.match(pattern, '1')
    assert re.match(pattern, '9999')
    assert not re.match(pattern, '0')
    assert not re.match(pattern, '01')


class TestValidateField:
  """Tests for validate_field: generic validator using VALIDATION_RULES."""

  def test_valid_locomotive_number(self):
    ok, msg = validate_field('locomotive_number', '0001')
    assert ok is True
    assert msg == ''

  def test_invalid_locomotive_number(self):
    ok, msg = validate_field('locomotive_number', 'abc')
    assert ok is False
    assert '机车号' in msg

  def test_valid_decoder_number(self):
    ok, msg = validate_field('decoder_number', '42')
    assert ok is True
    assert msg == ''

  def test_invalid_decoder_number(self):
    ok, msg = validate_field('decoder_number', '00')
    assert ok is False
    assert '编号' in msg

  def test_valid_trainset_number(self):
    ok, msg = validate_field('trainset_number', '001')
    assert ok is True
    assert msg == ''

  def test_invalid_trainset_number(self):
    ok, msg = validate_field('trainset_number', 'ab')
    assert ok is False
    assert '动车号' in msg

  def test_valid_car_number(self):
    ok, msg = validate_field('car_number', 'ABC-123')
    assert ok is True
    assert msg == ''

  def test_invalid_car_number(self):
    ok, msg = validate_field('car_number', 'A' * 21)
    assert ok is False
    assert '车辆号' in msg

  def test_unknown_field_passes(self):
    ok, msg = validate_field('unknown_field', 'anything')
    assert ok is True
    assert msg == ''

  def test_empty_value_passes(self):
    ok, msg = validate_field('locomotive_number', '')
    assert ok is True
    assert msg == ''

  def test_none_value_passes(self):
    ok, msg = validate_field('locomotive_number', None)
    assert ok is True
    assert msg == ''


# ============================================================
# price_calculator.py tests
# ============================================================

class TestSafeEval:
  """Tests for SafeEval AST-based expression evaluator."""

  def test_simple_addition(self):
    result = calculate_price('100+200')
    assert result == 300.0

  def test_simple_subtraction(self):
    result = calculate_price('500-200')
    assert result == 300.0

  def test_multiplication(self):
    result = calculate_price('10*20')
    assert result == 200.0

  def test_division(self):
    result = calculate_price('100/4')
    assert result == 25.0

  def test_complex_expression(self):
    result = calculate_price('288+538')
    assert result == 826.0

  def test_expression_with_parens(self):
    result = calculate_price('(10+20)*3')
    assert result == 90.0

  def test_negative_number(self):
    result = calculate_price('-5+10')
    assert result == 5.0

  def test_float_numbers(self):
    result = calculate_price('10.5+20.3')
    assert abs(result - 30.8) < 0.01

  def test_nested_parens(self):
    result = calculate_price('((2+3)*4)')
    assert result == 20.0

  def test_spaces_in_expression(self):
    result = calculate_price('100 + 200')
    assert result == 300.0

  def test_plain_number(self):
    result = calculate_price('42')
    assert result == 42

  def test_float_value(self):
    result = calculate_price(42.5)
    assert result == 42.5

  def test_integer_value(self):
    result = calculate_price(100)
    assert result == 100

  def test_empty_string_returns_zero(self):
    assert calculate_price('') == 0

  def test_none_returns_zero(self):
    assert calculate_price(None) == 0

  def test_whitespace_only_returns_zero(self):
    assert calculate_price('   ') == 0

  def test_division_by_zero_returns_zero(self):
    result = calculate_price('1/0')
    assert result == 0

  def test_invalid_expression_returns_zero(self):
    assert calculate_price('abc') == 0

  def test_code_injection_returns_zero(self):
    assert calculate_price("__import__('os').system('ls')") == 0

  def test_function_call_injection_returns_zero(self):
    # The regex check should reject expressions with quotes
    assert calculate_price("open('/etc/passwd')") == 0

  def test_import_injection_returns_zero(self):
    assert calculate_price("import os") == 0

  def test_non_numeric_string_returns_zero(self):
    assert calculate_price("'hello'") == 0

  def test_mixed_operations(self):
    result = calculate_price('2+3*4')
    assert result == 14.0

  def test_subtraction_and_addition(self):
    result = calculate_price('100-50+25')
    assert result == 75.0

  def test_unsafe_ast_node(self):
    """Directly test SafeEval with an unsafe AST node."""
    import ast
    evaluator = SafeEval()
    # Create a Call node which is not in the allowed list
    callNode = ast.Call(
      func=ast.Name(id='open', ctx=ast.Load()),
      args=[ast.Constant(value='/etc/passwd')],
      keywords=[]
    )
    with pytest.raises(ValueError, match="不安全的表达式节点"):
      evaluator.visit(callNode)

  def test_string_constant_rejected(self):
    """Test that a string constant is rejected by SafeEval."""
    import ast
    evaluator = SafeEval()
    constNode = ast.Constant(value='hello')
    with pytest.raises(ValueError, match="不支持的常量类型"):
      evaluator.visit(constNode)


# ============================================================
# helpers.py tests
# ============================================================

class TestParsePurchaseDate:
  """Tests for parse_purchase_date."""

  def test_valid_date_string(self):
    result = parse_purchase_date('2024-01-15')
    assert result == date(2024, 1, 15)

  def test_none_returns_today(self):
    result = parse_purchase_date(None)
    assert result == date.today()

  def test_empty_string_returns_today(self):
    result = parse_purchase_date('')
    assert result == date.today()

  def test_whitespace_string_returns_today(self):
    result = parse_purchase_date('   ')
    assert result == date.today()

  def test_datetime_object(self):
    dt = datetime(2024, 6, 15, 10, 30, 0)
    result = parse_purchase_date(dt)
    assert result == date(2024, 6, 15)

  def test_date_object(self):
    d = date(2024, 3, 20)
    result = parse_purchase_date(d)
    assert result == date(2024, 3, 20)

  def test_invalid_format_returns_today(self):
    result = parse_purchase_date('not-a-date')
    assert result == date.today()

  def test_partial_date_returns_today(self):
    result = parse_purchase_date('2024-13-45')
    assert result == date.today()

  def test_integer_input_returns_today(self):
    result = parse_purchase_date(12345)
    assert result == date.today()

  def test_year_month_only_returns_today(self):
    result = parse_purchase_date('2024-01')
    assert result == date.today()


class TestSafeInt:
  """Tests for safe_int."""

  def test_valid_integer(self):
    assert safe_int(42) == 42

  def test_string_integer(self):
    assert safe_int('42') == 42

  def test_negative_integer(self):
    assert safe_int(-5) == -5

  def test_none_returns_default(self):
    assert safe_int(None) is None

  def test_none_custom_default(self):
    assert safe_int(None, default=0) == 0

  def test_invalid_string(self):
    assert safe_int('abc') is None

  def test_float_truncates(self):
    assert safe_int(3.7) == 3

  def test_empty_string(self):
    assert safe_int('') is None

  def test_zero(self):
    assert safe_int(0) == 0

  def test_string_zero(self):
    assert safe_int('0') == 0

  def test_large_number(self):
    assert safe_int(999999) == 999999

  def test_boolean_input(self):
    # bool is a subclass of int in Python
    assert safe_int(True) == 1
    assert safe_int(False) == 0


class TestSafeFloat:
  """Tests for safe_float."""

  def test_valid_float(self):
    assert safe_float(3.14) == 3.14

  def test_string_float(self):
    assert safe_float('3.14') == 3.14

  def test_integer_input(self):
    assert safe_float(42) == 42.0

  def test_none_returns_default(self):
    assert safe_float(None) == 0.0

  def test_none_custom_default(self):
    assert safe_float(None, default=-1.0) == -1.0

  def test_invalid_string(self):
    assert safe_float('abc') == 0.0

  def test_empty_string(self):
    assert safe_float('') == 0.0

  def test_zero(self):
    assert safe_float(0) == 0.0

  def test_negative(self):
    assert safe_float(-2.5) == -2.5


class TestValidateUnique:
  """Tests for validate_unique with database."""

  def test_unique_brand_name(self, app):
    with app.app_context():
      brand = Brand(name='UniqueBrand', abbreviation='UB')
      db.session.add(brand)
      db.session.commit()

      result = validate_unique(Brand, 'name', 'OtherBrand')
      assert result is True

  def test_duplicate_brand_name(self, app):
    with app.app_context():
      brand = Brand(name='DuplicateBrand', abbreviation='DB')
      db.session.add(brand)
      db.session.commit()

      result = validate_unique(Brand, 'name', 'DuplicateBrand')
      assert result is False

  def test_exclude_self(self, app):
    with app.app_context():
      brand = Brand(name='ExcludeMe', abbreviation='EM')
      db.session.add(brand)
      db.session.commit()

      result = validate_unique(Brand, 'name', 'ExcludeMe', exclude_id=brand.id)
      assert result is True

  def test_exclude_different_id(self, app):
    with app.app_context():
      brand = Brand(name='NoExclude', abbreviation='NE')
      db.session.add(brand)
      db.session.commit()

      result = validate_unique(Brand, 'name', 'NoExclude', exclude_id=999)
      assert result is False

  def test_locomotive_number_unique_within_scale(self, app, sample_data):
    with app.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', locomotive_number='1234'
      )
      db.session.add(loco)
      db.session.commit()

      # Same number in same scale -> not unique
      assert validate_unique(Locomotive, 'locomotive_number', '1234', scale='HO') is False

      # Same number in different scale -> unique
      assert validate_unique(Locomotive, 'locomotive_number', '1234', scale='N') is True


class TestApiSuccess:
  """Tests for api_success response builder."""

  def test_default_message(self):
    result = api_success()
    assert result == {'success': True, 'message': '操作成功'}

  def test_custom_message(self):
    result = api_success(message='创建成功')
    assert result == {'success': True, 'message': '创建成功'}

  def test_with_data(self):
    result = api_success(message='ok', data={'id': 1, 'name': 'test'})
    assert result == {'success': True, 'message': 'ok', 'id': 1, 'name': 'test'}

  def test_with_none_data(self):
    result = api_success(data=None)
    assert result == {'success': True, 'message': '操作成功'}

  def test_with_empty_data(self):
    result = api_success(data={})
    assert result == {'success': True, 'message': '操作成功'}


class TestApiError:
  """Tests for api_error response builder."""

  def test_message_only(self):
    result = api_error(message='Something went wrong')
    assert result == {'success': False, 'error': 'Something went wrong'}

  def test_with_field(self):
    result = api_error(message='Invalid format', field='locomotive_number')
    assert result == {
      'success': False,
      'errors': [{'field': 'locomotive_number', 'message': 'Invalid format'}]
    }

  def test_with_errors_list(self):
    errors = [
      {'field': 'name', 'message': 'Required'},
      {'field': 'price', 'message': 'Must be positive'}
    ]
    result = api_error(message='Validation failed', errors=errors)
    assert result == {'success': False, 'errors': errors}

  def test_errors_list_takes_precedence(self):
    errors = [{'field': 'x', 'message': 'err'}]
    result = api_error(message='msg', field='f', errors=errors)
    assert result == {'success': False, 'errors': errors}


class TestParseBoolean:
  """Tests for parse_boolean."""

  def test_true_string(self):
    assert parse_boolean('true') is True

  def test_false_string(self):
    # 'false' is a truthy string, not in the positive set -> returns False
    assert parse_boolean('false') is False

  def test_one_string(self):
    assert parse_boolean('1') is True

  def test_zero_string(self):
    # '0' is a truthy string, not in the positive set -> returns False
    assert parse_boolean('0') is False

  def test_yes_string(self):
    assert parse_boolean('yes') is True

  def test_chinese_yes(self):
    assert parse_boolean('是') is True

  def test_chinese_has(self):
    assert parse_boolean('有') is True

  def test_bool_true(self):
    assert parse_boolean(True) is True

  def test_bool_false(self):
    assert parse_boolean(False) is None

  def test_none(self):
    assert parse_boolean(None) is None

  def test_empty_string(self):
    assert parse_boolean('') is None

  def test_random_string(self):
    # 'random' is truthy string, not in positive set -> returns False
    assert parse_boolean('random') is False

  def test_uppercase_true(self):
    assert parse_boolean('TRUE') is True

  def test_mixed_case_true(self):
    assert parse_boolean('True') is True


class TestGenerateBrandAbbreviation:
  """Tests for generate_brand_abbreviation."""

  def test_chinese_name(self):
    # Chinese names use pypinyin to get first letter of each character
    # 测(C) 试(S) 品(P) 牌(P) -> CSPP
    result = generate_brand_abbreviation('测试品牌')
    assert result == 'CSPP'

  def test_single_chinese_char(self):
    result = generate_brand_abbreviation('测')
    assert result == 'C'

  def test_english_short_name(self):
    # English <= 6 chars: return uppercase
    result = generate_brand_abbreviation('Kato')
    assert result == 'KATO'

  def test_english_exactly_six_chars(self):
    # 'TomixX' splits as ['Tomix', 'X'] -> two words -> 'TX'
    result = generate_brand_abbreviation('TomixX')
    assert result == 'TX'

  def test_english_long_single_word(self):
    # English > 6 chars single word: return first 3 uppercase
    result = generate_brand_abbreviation('Microtrain')
    assert result == 'MIC'

  def test_camel_case_name(self):
    # camelCase / PascalCase: first letter of each word
    result = generate_brand_abbreviation('MicroTrain')
    assert result == 'MT'

  def test_pascal_case_multiple_words(self):
    result = generate_brand_abbreviation('TrainModelManager')
    assert result == 'TMM'

  def test_empty_string(self):
    assert generate_brand_abbreviation('') == ''

  def test_none(self):
    assert generate_brand_abbreviation(None) == ''

  def test_english_all_caps_short(self):
    result = generate_brand_abbreviation('ABC')
    assert result == 'ABC'

  def test_mixed_case_two_words(self):
    result = generate_brand_abbreviation('TomyTec')
    # TomyTec splits as ['Tomy', 'Tec'] -> 'TT'
    assert result == 'TT'

  def test_numeric_suffix(self):
    # Name with numbers
    result = generate_brand_abbreviation('Model123')
    # Splits as ['Model', '123'] -> 'M1'
    assert result == 'M1'


# ============================================================
# routes/system.py tests
# ============================================================

class TestSystemRoute:
  """Tests for system maintenance page route."""

  def test_system_page_renders(self, client):
    """Test GET /system returns the system page."""
    response = client.get('/system')
    assert response.status_code == 200

  def test_reinit_database_success(self, client, sample_data):
    """Test POST /system/reinit with mocked subprocess."""
    with patch('routes.system.subprocess.run') as mockRun:
      mockRun.return_value = MagicMock(returncode=0)
      response = client.post('/system/reinit', headers={'X-Confirm': 'REINIT'})
      assert response.status_code == 200
      data = response.get_json()
      assert data['success'] is True
      assert '成功' in data['message']
      mockRun.assert_called_once()

  def test_reinit_database_subprocess_failure(self, client, sample_data):
    """Test POST /system/reinit when subprocess fails."""
    with patch('routes.system.subprocess.run') as mockRun:
      mockRun.side_effect = Exception('Script not found')
      response = client.post('/system/reinit', headers={'X-Confirm': 'REINIT'})
      assert response.status_code == 500
      data = response.get_json()
      assert data['success'] is False

  def test_reinit_database_clears_models(self, client, sample_data):
    """Test that reinit clears existing model data before subprocess."""
    with client.application.app_context():
      # Add a locomotive record
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', locomotive_number='9999'
      )
      db.session.add(loco)
      db.session.commit()
      assert Locomotive.query.count() == 1

    with patch('routes.system.subprocess.run') as mockRun:
      mockRun.return_value = MagicMock(returncode=0)
      client.post('/system/reinit', headers={'X-Confirm': 'REINIT'})

    # After reinit, data should be cleared (subprocess is mocked so no re-insert)
    with client.application.app_context():
      assert Locomotive.query.count() == 0


# ============================================================
# routes/main.py tests
# ============================================================

class TestMainRoute:
  """Tests for main index route."""

  def test_index_page_renders(self, client):
    """Test GET / returns the index page."""
    response = client.get('/')
    assert response.status_code == 200

  def test_statistics_empty_db(self, client):
    """Test GET /api/statistics with empty database."""
    response = client.get('/api/statistics')
    assert response.status_code == 200
    data = response.get_json()
    assert 'type_stats' in data
    assert 'scale_stats' in data
    assert 'brand_stats' in data
    assert 'merchant_stats' in data

    # All counts should be 0
    for typeKey, typeData in data['type_stats'].items():
      assert typeData['count'] == 0
      assert typeData['total'] == 0

  def test_statistics_with_locomotive(self, client, sample_data):
    """Test statistics include locomotive data."""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', total_price=500.0
      )
      db.session.add(loco)
      db.session.commit()

    response = client.get('/api/statistics')
    data = response.get_json()
    assert data['type_stats']['locomotive']['count'] == 1
    assert data['type_stats']['locomotive']['total'] == 500.0

  def test_statistics_with_carriage_set(self, client, sample_data):
    """Test statistics include carriage set data."""
    with client.application.app_context():
      carriageSet = CarriageSet(
        brand_id=1, series_id=1, scale='HO', total_price=300.0
      )
      db.session.add(carriageSet)
      db.session.commit()

    response = client.get('/api/statistics')
    data = response.get_json()
    assert data['type_stats']['carriage']['count'] == 1
    assert data['type_stats']['carriage']['total'] == 300.0

  def test_statistics_with_trainset(self, client, sample_data):
    """Test statistics include trainset data."""
    with client.application.app_context():
      trainset = Trainset(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='N', total_price=800.0
      )
      db.session.add(trainset)
      db.session.commit()

    response = client.get('/api/statistics')
    data = response.get_json()
    assert data['type_stats']['trainset']['count'] == 1
    assert data['type_stats']['trainset']['total'] == 800.0

  def test_statistics_with_locomotive_head(self, client, sample_data):
    """Test statistics include locomotive head data."""
    with client.application.app_context():
      head = LocomotiveHead(
        model_id=1, brand_id=1, scale='HO', total_price=200.0
      )
      db.session.add(head)
      db.session.commit()

    response = client.get('/api/statistics')
    data = response.get_json()
    assert data['type_stats']['locomotive_head']['count'] == 1
    assert data['type_stats']['locomotive_head']['total'] == 200.0

  def test_statistics_scale_grouping(self, client, sample_data):
    """Test statistics group by scale correctly."""
    with client.application.app_context():
      loco1 = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', total_price=500.0
      )
      loco2 = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='N', total_price=300.0
      )
      db.session.add_all([loco1, loco2])
      db.session.commit()

    response = client.get('/api/statistics')
    data = response.get_json()
    assert 'HO' in data['scale_stats']
    assert 'N' in data['scale_stats']
    assert data['scale_stats']['HO']['count'] == 1
    assert data['scale_stats']['HO']['total'] == 500.0
    assert data['scale_stats']['N']['count'] == 1
    assert data['scale_stats']['N']['total'] == 300.0

  def test_statistics_brand_grouping(self, client, sample_data):
    """Test statistics group by brand correctly."""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', total_price=500.0
      )
      db.session.add(loco)
      db.session.commit()

    response = client.get('/api/statistics')
    data = response.get_json()
    assert '测试品牌' in data['brand_stats']
    assert data['brand_stats']['测试品牌']['count'] == 1
    assert data['brand_stats']['测试品牌']['total'] == 500.0

  def test_statistics_merchant_grouping(self, client, sample_data):
    """Test statistics group by merchant correctly."""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', merchant_id=1, total_price=400.0
      )
      db.session.add(loco)
      db.session.commit()

    response = client.get('/api/statistics')
    data = response.get_json()
    assert '测试商家' in data['merchant_stats']
    assert data['merchant_stats']['测试商家']['count'] == 1
    assert data['merchant_stats']['测试商家']['total'] == 400.0

  def test_statistics_model_without_brand(self, client, sample_data):
    """Test statistics handle model without brand (brand_id=None)."""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=None,
        scale='HO', total_price=100.0
      )
      db.session.add(loco)
      db.session.commit()

    response = client.get('/api/statistics')
    data = response.get_json()
    assert '未知' in data['brand_stats']
    assert data['brand_stats']['未知']['count'] == 1

  def test_statistics_model_without_merchant(self, client, sample_data):
    """Test statistics handle model without merchant (merchant_id=None)."""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', merchant_id=None, total_price=100.0
      )
      db.session.add(loco)
      db.session.commit()

    response = client.get('/api/statistics')
    data = response.get_json()
    assert '未知' in data['merchant_stats']

  def test_statistics_null_total_price(self, client, sample_data):
    """Test statistics handle null total_price."""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', total_price=None
      )
      db.session.add(loco)
      db.session.commit()

    response = client.get('/api/statistics')
    data = response.get_json()
    assert data['type_stats']['locomotive']['count'] == 1
    assert data['type_stats']['locomotive']['total'] == 0

  def test_statistics_multiple_types(self, client, sample_data):
    """Test statistics with multiple model types."""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', total_price=500.0
      )
      trainset = Trainset(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', total_price=800.0
      )
      db.session.add_all([loco, trainset])
      db.session.commit()

    response = client.get('/api/statistics')
    data = response.get_json()
    assert data['type_stats']['locomotive']['count'] == 1
    assert data['type_stats']['trainset']['count'] == 1
    assert data['type_stats']['carriage']['count'] == 0
    assert data['type_stats']['locomotive_head']['count'] == 0
    # HO scale should have 2 items
    assert data['scale_stats']['HO']['count'] == 2
    assert data['scale_stats']['HO']['total'] == 1300.0

  def test_statistics_type_names(self, client):
    """Test that type_stats has correct Chinese names."""
    response = client.get('/api/statistics')
    data = response.get_json()
    assert data['type_stats']['locomotive']['name'] == '机车模型'
    assert data['type_stats']['carriage']['name'] == '车厢模型'
    assert data['type_stats']['trainset']['name'] == '动车组模型'
    assert data['type_stats']['locomotive_head']['name'] == '先头车模型'
