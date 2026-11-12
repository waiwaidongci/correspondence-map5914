-- 002_run_input_snapshot.sql  (PostgreSQL)
-- 对应分析固化提交当时的输入，避免研究员后续校订计数/类别导致历史结果依据漂移。
-- correspondence_runs 新增：
--   input_snapshot    JSON       提交当时的研究/类别/计数/矩阵快照
--   input_fingerprint VARCHAR(64) 由提交当时输入计算的SHA-256，重复提交去重并作为结果指纹
-- 历史运行两列为空：worker 回落实时表并即时补算指纹；这些运行不支持沿用快照重试。
ALTER TABLE correspondence_runs
    ADD COLUMN IF NOT EXISTS input_snapshot JSON DEFAULT '{}';

ALTER TABLE correspondence_runs
    ADD COLUMN IF NOT EXISTS input_fingerprint VARCHAR(64) DEFAULT '';

CREATE INDEX IF NOT EXISTS ix_correspondence_runs_input_fingerprint
    ON correspondence_runs (input_fingerprint);
