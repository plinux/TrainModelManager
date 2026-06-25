"""
室内灯种子数据单一来源（P2-3）

init_db.py 与 seed_light_data.py 共用此模块，消除两份逐行重复的灯数据定义。
本函数不 commit，由调用方决定提交时机（init_db 在新库上，seed_light_data.py 先清理）。
"""
from models import (
  db, Brand, CarriageModel,
  LightBrand, LightModel, LightModelCarriage, LightModelBrandApplicability,
)


def seed_light_data():
  """填充室内灯品牌、型号和适用车型关联。

  前置：灯相关表已清空（init_db 新库，或 seed_light_data.py 已 query.delete）。
  本函数只 add，不 commit。
  """
  # 灯品牌
  light_brand_defs = [
    ('PIKO', 'HO'), ('ROCO', 'HO'), ('KATO', 'N'),
    ('TOMIX', 'N'), ('铁制所', 'N'), ('半岛急行', 'N'), ('见微', 'N'),
  ]
  lb_id_map = {}
  for name, _scale in light_brand_defs:
    lb = LightBrand(name=name)
    db.session.add(lb)
    db.session.flush()
    lb_id_map[name] = lb.id

  brand_id_map = {b.id: b.name for b in Brand.query.all()}
  kato_compat = [bid for bid, n in brand_id_map.items() if n in ('KATO', 'Kunter', '长鸣')]
  tomix_compat = [bid for bid, n in brand_id_map.items() if n in ('Tomix', 'MicroAce')]

  # 车厢车型分类：RW/CA/KD → TYPE2 专用；其他 → TYPE1
  rw_ca_kd_keywords = ('rw', 'ca', 'kd')
  kunter_rw_ca_kd_ids = []
  other_carriage_ids = []
  for cm in CarriageModel.query.order_by(CarriageModel.id).all():
    if any(cm.name.lower().startswith(kw) for kw in rw_ca_kd_keywords):
      kunter_rw_ca_kd_ids.append(cm.id)
    else:
      other_carriage_ids.append(cm.id)

  def add_lm(name, color_temp, lb_key, scale):
    lm = LightModel(name=name, color_temperature=color_temp,
                    light_brand_id=lb_id_map[lb_key], scale=scale)
    db.session.add(lm)
    db.session.flush()
    return lm.id

  def add_brand_level_app(light_model_id, model_brand_ids, vehicle_type='all'):
    for brand_id in model_brand_ids:
      db.session.add(LightModelBrandApplicability(
        light_model_id=light_model_id, brand_id=brand_id, vehicle_type=vehicle_type))

  def add_carriage_app(light_model_id, model_brand_ids, carriage_model_ids):
    for brand_id in model_brand_ids:
      for cm_id in carriage_model_ids:
        db.session.add(LightModelCarriage(
          light_model_id=light_model_id, carriage_model_id=cm_id, brand_id=brand_id))

  lm = {}
  lm['piko_oem'] = add_lm('PIKO-原厂', '5000K', 'PIKO', 'HO')
  lm['roco_oem'] = add_lm('ROCO-原厂', '5000K', 'ROCO', 'HO')
  lm['kato_11_212'] = add_lm('KATO 11-212', '5000K', 'KATO', 'N')
  lm['kato_11_214'] = add_lm('KATO 11-214', '5000K', 'KATO', 'N')

  bdjx_temps = ['3000K', '4000K', '5000K', '6000K']
  for temp in bdjx_temps:
    for conn in ['KATO', 'TOMIX']:
      lm[f'bdjx_t1_{conn.lower()}_{temp}'] = add_lm(f'BDJX_{temp}_{conn}', temp, '半岛急行', 'N')
      lm[f'bdjx_t2_{conn.lower()}_{temp}'] = add_lm(f'BDJX_{temp}_TYPE2_{conn}', temp, '半岛急行', 'N')
  for temp in ['3000K', '5000K']:
    lm[f'bdjx_t2w_tomix_{temp}'] = add_lm(f'BDJX_{temp}_TYPE2_宽幅_TOMIX', temp, '半岛急行', 'N')

  for jt in ['KLV', 'TC', 'TLC']:
    for temp in ['3000K', '4000K', '5000K']:
      lm[f'jw_{jt.lower()}_{temp}'] = add_lm(f'JWMR-{jt}-{temp}', temp, '见微', 'N')

  piko_brands = [bid for bid, n in brand_id_map.items() if n == 'PIKO']
  roco_brands = [bid for bid, n in brand_id_map.items() if n == 'ROCO']
  kato_brands = [bid for bid, n in brand_id_map.items() if n == 'KATO']
  kunter_brands = [bid for bid, n in brand_id_map.items() if n == 'Kunter']

  add_brand_level_app(lm['piko_oem'], piko_brands, 'all')
  add_brand_level_app(lm['roco_oem'], roco_brands, 'all')
  add_brand_level_app(lm['kato_11_212'], kato_brands, 'all')
  add_brand_level_app(lm['kato_11_214'], kato_brands, 'all')

  for temp in bdjx_temps:
    add_carriage_app(lm[f'bdjx_t1_kato_{temp}'], kato_compat, other_carriage_ids)
    add_carriage_app(lm[f'bdjx_t1_tomix_{temp}'], tomix_compat, other_carriage_ids)
    add_carriage_app(lm[f'bdjx_t2_kato_{temp}'], kunter_brands, kunter_rw_ca_kd_ids)
    add_carriage_app(lm[f'bdjx_t2_tomix_{temp}'], kunter_brands, kunter_rw_ca_kd_ids)
  for temp in ['3000K', '5000K']:
    add_carriage_app(lm[f'bdjx_t2w_tomix_{temp}'], kunter_brands, kunter_rw_ca_kd_ids)

  for temp in ['3000K', '4000K', '5000K']:
    add_brand_level_app(lm[f'jw_klv_{temp}'], kato_compat, 'carriage')
  for jt in ['tc', 'tlc']:
    for temp in ['3000K', '4000K', '5000K']:
      add_brand_level_app(lm[f'jw_{jt}_{temp}'], tomix_compat, 'carriage')
