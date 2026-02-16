"""
系统维护路由
提供数据导入导出和数据库初始化功能
"""
from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from models import db, PowerType, Brand, Depot, Merchant, ChipInterface, ChipModel
from models import LocomotiveSeries, LocomotiveModel, CarriageSeries, CarriageModel
from models import TrainsetSeries, TrainsetModel
import subprocess
import logging

logger = logging.getLogger(__name__)

system_bp = Blueprint('system', __name__)


@system_bp.route('/system')
def system():
    """系统维护页面"""
    return render_template('system.html')


@system_bp.route('/system/reinit', methods=['POST'])
def reinit_database():
    """重新初始化数据库"""
    try:
        # 删除所有数据（按外键依赖顺序）
        from models import CarriageItem, Locomotive, CarriageSet, Trainset, LocomotiveHead
        CarriageItem.query.delete()
        Locomotive.query.delete()
        CarriageSet.query.delete()
        Trainset.query.delete()
        LocomotiveHead.query.delete()
        LocomotiveModel.query.delete()
        TrainsetModel.query.delete()
        CarriageModel.query.delete()
        LocomotiveSeries.query.delete()
        CarriageSeries.query.delete()
        TrainsetSeries.query.delete()
        ChipModel.query.delete()
        ChipInterface.query.delete()
        Depot.query.delete()
        Merchant.query.delete()
        Brand.query.delete()
        PowerType.query.delete()
        db.session.commit()

        # 运行初始化脚本
        subprocess.run(['python', 'init_db.py'], check=True)

        logger.info("Database reinitialized successfully")
        return jsonify({'success': True, 'message': '数据库重新初始化成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error reinitializing database: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
