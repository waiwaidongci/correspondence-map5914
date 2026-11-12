from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import String,JSON,ForeignKey,DateTime,Index
from datetime import datetime,timezone
from src.config.database import Base
class CorrespondenceRun(Base):
 __tablename__='correspondence_runs'
 __table_args__=(Index('ix_correspondence_runs_input_fingerprint','input_fingerprint'),)
 id:Mapped[int]=mapped_column(primary_key=True)
 study_id:Mapped[int]=mapped_column(ForeignKey('contingency_studies.id'))
 name:Mapped[str]=mapped_column(String(100))
 axes:Mapped[int]=mapped_column(default=2)
 status:Mapped[str]=mapped_column(String(20),default='queued')
 result:Mapped[dict]=mapped_column(JSON,default=dict)
 error:Mapped[str|None]=mapped_column(String(1000),nullable=True)
 # 提交当时固化的输入：计数与类别快照，后续校订不回写历史运行
 input_snapshot:Mapped[dict]=mapped_column(JSON,default=dict)
 # 由提交当时输入计算的SHA-256，重复提交据此去重；同时作为结果指纹
 input_fingerprint:Mapped[str]=mapped_column(String(64),default='')
 creator_id:Mapped[int]=mapped_column(ForeignKey('users.id'))
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
