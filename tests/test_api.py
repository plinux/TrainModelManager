"""
API 测试
验证 Excel 导入导出和自动填充功能
"""
import pytest
import io
import openpyxl
from openpyxl import Workbook


class TestExcelExport:
    """Excel 导出测试"""

    def test_export_excel_success(self, client, sample_data):
        """测试 Excel 导出成功"""
        from models import db, Locomotive

        with client.application.app_context():
            # 添加一个机车以便有数据导出
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                locomotive_number='0001'
            )
            db.session.add(loco)
            db.session.commit()

        response = client.get('/api/export/excel')
        assert response.status_code == 200
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.content_type

    def test_export_excel_empty(self, client):
        """测试空数据库导出"""
        response = client.get('/api/export/excel')
        # 空数据库应该返回错误
        assert response.status_code == 400

    def test_export_locomotive_head_no_depot(self, client, sample_data):
        """测试先头车导出不包含动车段列"""
        from models import db, LocomotiveHead

        with client.application.app_context():
            head = LocomotiveHead(
                model_id=1,
                brand_id=1,
                scale='HO',
                head_light=True,
                special_color='红色'
            )
            db.session.add(head)
            db.session.commit()

        response = client.get('/api/export/excel')
        assert response.status_code == 200

        # 解析 Excel 检查列头
        wb = openpyxl.load_workbook(io.BytesIO(response.data))
        if '先头车' in wb.sheetnames:
            sheet = wb['先头车']
            headers = [cell.value for cell in sheet[1]]
            # 确保没有动车段
            assert '动车段' not in headers
            # 确保有涂装（原特涂）
            assert '涂装' in headers


class TestExcelImport:
    """Excel 导入测试"""

    def test_import_locomotive_head_no_depot(self, client, sample_data):
        """测试先头车导入（无动车段）"""
        # 创建测试 Excel
        wb = Workbook()
        ws = wb.create_sheet('先头车')
        ws.append(['车型', '品牌', '涂装', '比例', '头车灯', '室内灯', '价格', '总价', '货号', '购买日期', '购买商家'])
        ws.append(['CRH380A', '测试品牌', '红色', 'HO', '是', 'LED', '100', '100', '001', '', ''])

        # 移除默认 sheet
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])

        # 保存到内存
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)

        response = client.post(
            '/api/import/excel',
            data={'file': (excel_file, 'test.xlsx')},
            content_type='multipart/form-data'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data.get('success') == True


class TestAutoFillAPI:
    """自动填充 API 测试"""

    def test_auto_fill_locomotive(self, client, sample_data):
        """测试机车自动填充"""
        response = client.get('/api/auto-fill/locomotive/1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'series_id' in data
        assert 'power_type_id' in data

    def test_auto_fill_trainset(self, client, sample_data):
        """测试动车组自动填充"""
        response = client.get('/api/auto-fill/trainset/1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'series_id' in data
        assert 'power_type_id' in data


class TestStatisticsAPI:
    """统计 API 测试"""

    def test_statistics_endpoint(self, client):
        """测试统计 API"""
        response = client.get('/api/statistics')
        assert response.status_code == 200
        data = response.get_json()
        assert 'type_stats' in data
        assert 'scale_stats' in data
        assert 'brand_stats' in data
        assert 'merchant_stats' in data
