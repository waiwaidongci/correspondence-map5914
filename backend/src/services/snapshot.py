from sqlalchemy import select
from fastapi import HTTPException
from src.models import ContingencyStudy,Category,CellCount
from src.utils.serialize import row
from .fingerprint import fingerprint


def capture_snapshot(db,study_id,axes):
 """在提交当时固化研究、类别与计数；worker与解释/导出一律以此为唯一依据。"""
 study=db.get(ContingencyStudy,study_id)
 if not study:
  raise HTTPException(404,'列联研究不存在')
 rows=[row(x) for x in db.scalars(select(Category).where(Category.study_id==study_id,Category.axis=='row').order_by(Category.code))]
 cols=[row(x) for x in db.scalars(select(Category).where(Category.study_id==study_id,Category.axis=='column').order_by(Category.code))]
 cells=[row(x) for x in db.scalars(select(CellCount).where(CellCount.study_id==study_id))]
 lookup={(x['row_id'],x['column_id']):x['count'] for x in cells}
 table=[[lookup.get((r['id'],c['id']),0) for c in cols] for r in rows]
 snapshot={'study':row(study),'axes':axes,'rows':rows,'columns':cols,'cells':cells,'table':table}
 snapshot['fingerprint']=fingerprint(snapshot['study'],rows,cols,cells,axes)
 return snapshot


def snapshot_table(snapshot):
 """从快照重建table_data等价的(study,rows,cols,cells,table)，绝不读取实时校订值。"""
 return snapshot['study'],snapshot['rows'],snapshot['columns'],snapshot['cells'],snapshot['table']
