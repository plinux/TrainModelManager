import pytest
from utils.helpers import generate_brand_abbreviation


class TestGenerateBrandAbbreviation:
    """测试品牌缩写生成规则"""

    def test_chinese_brand(self):
        """中文品牌：每个汉字拼音首字母大写"""
        assert generate_brand_abbreviation('百万城') == 'BWC'
        assert generate_brand_abbreviation('浩瀚') == 'HH'
        assert generate_brand_abbreviation('深东') == 'SD'

    def test_english_short_brand(self):
        """英文品牌≤6字母：直接使用原名称大写"""
        assert generate_brand_abbreviation('Kunter') == 'KUNTER'
        assert generate_brand_abbreviation('KATO') == 'KATO'
        assert generate_brand_abbreviation('BLI') == 'BLI'
        assert generate_brand_abbreviation('N27') == 'N27'

    def test_english_long_brand(self):
        """英文品牌>6字母：前3个字母大写（非 camelCase）"""
        assert generate_brand_abbreviation('Fleischmann') == 'FLE'
        assert generate_brand_abbreviation('WALTHERS') == 'WAL'
        # MicroAce 是 PascalCase，会被识别为多词
        assert generate_brand_abbreviation('Rivarossi') == 'RIV'

    def test_multi_word_brand_camelcase(self):
        """多词英文(camelCase)：每个单词首字母"""
        assert generate_brand_abbreviation('KukePig') == 'KP'

    def test_english_with_numbers(self):
        """英文含数字：按短品牌处理"""
        assert generate_brand_abbreviation('1435') == '1435'
        assert generate_brand_abbreviation('HCMX') == 'HCMX'

    def test_empty_string(self):
        """空字符串返回空"""
        assert generate_brand_abbreviation('') == ''
