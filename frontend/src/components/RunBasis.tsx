import {useState} from 'react';
import type {Run} from '../types/domain';
import {Table} from './common/Table';

// 展示该次分析提交当时固化的计数与类别；后续校订不回写，页面可据此核对依据。
export function RunBasis({run}:{run:Run}){
 const [open,setOpen]=useState(false);
 const snap=run.input_snapshot;
 const fingerprint=run.input_fingerprint||snap?.fingerprint||run.result.fingerprint||'';
 if(!snap){
  return <section className="run-basis"><header><small>SUBMISSION BASIS / 分析依据（提交当时快照）</small><span className="diagnostic-label sparse">历史运行无快照</span></header><p>该运行在快照功能上线前建立，结果依据实时表计算，无法逐格核对提交当时计数。</p></section>;
 }
 const total=snap.table.reduce((n,row)=>n+row.reduce((a,b)=>a+b,0),0);
 return (
  <section className="run-basis">
   <header>
    <div>
     <small>SUBMISSION BASIS / 分析依据（提交当时固化，后续校订不影响本次）</small>
     <h2>{snap.study.name} · N={total} · {snap.rows.length}×{snap.columns.length}</h2>
    </div>
    <button className="text-button" onClick={()=>setOpen(v=>!v)}>{open?'收起计数矩阵 ↙':'核对提交当时计数 ↗'}</button>
   </header>
   <p className="basis-fingerprint">输入指纹 SHA-256 <code>{fingerprint}</code>；重复提交同一输入不会重复发布，失败重试沿用此快照。</p>
   {open&&(
    <div className="table-wrap">
     <Table headers={['提交当时类别',...snap.columns.map(c=>c.code+' / '+c.label)]}>
      {snap.table.map((vals,i)=>(
       <tr key={snap.rows[i].id}>
        <td><small>{snap.rows[i].code}</small><strong>{snap.rows[i].label}</strong></td>
        {vals.map((v,j)=><td key={snap.columns[j].id} className="count-cell"><strong>{v}</strong></td>)}
       </tr>
      ))}
     </Table>
     <p className="fine">行类别：{snap.rows.map(r=>r.code+' '+r.label).join('、')}；列类别：{snap.columns.map(c=>c.code+' '+c.label).join('、')}。来源文件 {snap.study.filename}。</p>
    </div>
   )}
  </section>
 );
}
