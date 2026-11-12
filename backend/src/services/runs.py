from sqlalchemy import select
from fastapi import HTTPException
from src.models import CorrespondenceRun,ContingencyStudy
from src.constants.enums import RunStatus
from src.utils.serialize import row
from .audit import record
from .snapshot import capture_snapshot

def list_runs(db):return [row(x) for x in db.scalars(select(CorrespondenceRun).order_by(CorrespondenceRun.id.desc()))]
def get_run(db,id):
 obj=db.get(CorrespondenceRun,id)
 if not obj:raise HTTPException(404,'对应分析不存在')
 return obj

def _enqueue(run):
 from src.worker import analyze_run
 try:
  analyze_run.delay(run.id)
  return True
 except Exception:
  run.status=RunStatus.FAILED;run.error='队列不可用'
  return False

def _fresh(db,obj):
 # worker在独立会话提交状态，回到请求会话需重新加载，避免返回过期的queued状态
 db.expire_all()
 return row(db.get(CorrespondenceRun,obj.id))

def create_run(db,data,user):
 if not db.get(ContingencyStudy,data.study_id):raise HTTPException(404,'列联研究不存在')
 # 先固化提交当时的计数与类别，再做指纹去重，保证依据不随后续校订漂移
 snapshot=capture_snapshot(db,data.study_id,data.axes)
 digest=snapshot['fingerprint']
 existing=db.scalars(select(CorrespondenceRun).where(CorrespondenceRun.input_fingerprint==digest).order_by(CorrespondenceRun.id)).all()
 if existing:
  # 同一输入不重复发布：成功/排队/运行中的运行直接复用；失败运行沿用原输入重试
  reusable=next((r for r in existing if r.status!=RunStatus.FAILED),None)
  if reusable:
   record(db,user.email,'ca.reused',{'run_id':reusable.id,'input_fingerprint':digest})
   return {'reused':True,'run':_fresh(db,reusable)}
  target=existing[0]
  target.status=RunStatus.QUEUED;target.error=None
  if not _enqueue(target):
   db.commit();raise HTTPException(503,target.error)
  db.commit();record(db,user.email,'ca.retried',{'run_id':target.id,'input_fingerprint':digest})
  return {'reused':False,'retried':True,'run':_fresh(db,target)}
 obj=CorrespondenceRun(study_id=data.study_id,name=data.name,axes=data.axes,creator_id=user.id,input_snapshot=snapshot,input_fingerprint=digest)
 db.add(obj);db.commit()
 if not _enqueue(obj):
  db.commit();raise HTTPException(503,obj.error)
 record(db,user.email,'ca.queued',{'run_id':obj.id,'input_fingerprint':digest})
 return {'reused':False,'run':_fresh(db,obj)}

def retry_run(db,id,user):
 obj=db.get(CorrespondenceRun,id)
 if not obj:raise HTTPException(404,'对应分析不存在')
 if obj.status!=RunStatus.FAILED:raise HTTPException(409,'仅失败分析可重试')
 if not obj.input_snapshot or not obj.input_fingerprint:
  raise HTTPException(409,'历史运行缺少提交快照，无法沿用原输入，请重新提交分析')
 # 沿用提交当时的输入快照，不重新读取实时计数与类别
 obj.status=RunStatus.QUEUED;obj.error=None
 if not _enqueue(obj):
  db.commit();raise HTTPException(503,obj.error)
 db.commit();record(db,user.email,'ca.retried',{'run_id':obj.id,'input_fingerprint':obj.input_fingerprint})
 return {'reused':False,'retried':True,'run':_fresh(db,obj)}
