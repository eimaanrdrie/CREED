from __future__ import annotations
from typing import Any, Literal
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.domain import get_domain_db
from app.core.config import get_settings
from app.domain.models import AgentRun, AnalysisImpactAssessment, Client, DeliveryMethod, HumanDecision, Implementation, Investigation, InvestigationDetail, LearningProposal, LearningProposalDetail, MethodVersion, RecallNotice, SupportIssue
from app.services.advanced import *
from app.services.demo import demo_readiness, demo_status, reset_demo
from app.services.authority_enforcement import AuthorityCapability, AuthorityEnforcementError, require_human_authority

router=APIRouter(tags=["creed-intelligence"])

def _run(db:Session,graph_run_id:str)->AgentRun:
    r=db.scalar(select(AgentRun).where(AgentRun.graph_run_id==graph_run_id))
    if not r: raise HTTPException(404,"ANALYSIS_RUN_NOT_FOUND")
    return r

def _err(exc:Exception):
    raise HTTPException(422,str(exc))


def _authority_or_403(db: Session, principal: str | None, capability: AuthorityCapability, reviewer: str):
    try:
        return require_human_authority(
            db,
            principal=principal,
            capability=capability,
            claimed_reviewer=reviewer,
        )
    except AuthorityEnforcementError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

@router.post('/analysis-runs/{graph_run_id}/evidence/discover')
def discover(graph_run_id:str,db:Session=Depends(get_domain_db)):
    try:return discover_evidence(db,_run(db,graph_run_id))
    except Exception as e:_err(e)

@router.get('/analysis-runs/{graph_run_id}/evidence')
def evidence(graph_run_id:str,db:Session=Depends(get_domain_db)):
    return serialize_evidence_hits(db,_run(db,graph_run_id).id)

@router.get('/knowledge-graph/method-versions')
def versions(db:Session=Depends(get_domain_db)):
    rows=db.scalars(select(MethodVersion).order_by(MethodVersion.created_at.desc())).all()
    out=[]
    for v in rows:
        m=db.get(DeliveryMethod,v.method_id)
        out.append({
            'id':v.id,
            'version':v.version,
            'status':v.status,
            'method_id':v.method_id,
            'method_name':m.name if m else None,
            'adoption_policy':adoption_policy_for_version(db,v.id),
        })
    return out

@router.get('/knowledge-graph/method-versions/{version_id}/abom')
def abom(version_id:str,db:Session=Depends(get_domain_db)):
    try:return method_abom(db,version_id)
    except Exception as e:_err(e)

class EdgeCreate(BaseModel):
    source_type:str;source_id:str;target_type:str;target_id:str;relationship:str;confidence:float=Field(default=1.0,ge=0,le=1);evidence_document_id:str|None=None
@router.post('/knowledge-graph/edges')
def edge(payload:EdgeCreate,db:Session=Depends(get_domain_db)):
    try:
        e=create_edge(db,**payload.model_dump());return {'id':e.id,'relationship':e.relationship,'confidence':e.confidence}
    except Exception as ex:_err(ex)

@router.post('/analysis-runs/{graph_run_id}/impact')
def impact(graph_run_id:str,db:Session=Depends(get_domain_db)):
    try:return score_blast_radius(db,_run(db,graph_run_id))
    except Exception as e:_err(e)
@router.get('/analysis-runs/{graph_run_id}/impact')
def impact_get(graph_run_id:str,db:Session=Depends(get_domain_db)):
    return serialize_impact(db,_run(db,graph_run_id).id)

@router.post('/analysis-runs/{graph_run_id}/investigations')
def investigate(graph_run_id:str,db:Session=Depends(get_domain_db)):
    try:return run_investigations(db,_run(db,graph_run_id))
    except Exception as e:_err(e)
@router.get('/analysis-runs/{graph_run_id}/investigations')
def investigations(graph_run_id:str,db:Session=Depends(get_domain_db)):
    run=_run(db,graph_run_id);rows=investigations_for_run(db,run.id);out=[]
    for inv in rows:
        impl=db.get(Implementation,inv.implementation_id);client=db.get(Client,impl.client_id) if impl else None;finding=inv.findings[-1] if inv.findings else None;dec=inv.decisions[-1] if inv.decisions else None
        detail=db.scalar(select(InvestigationDetail).where(InvestigationDetail.investigation_id==inv.id))
        comparison=(detail.model_output_json or {}).get('configuration_comparison') if detail else None
        out.append({'id':inv.id,'implementation_id':inv.implementation_id,'implementation_name':impl.name if impl else None,'client_name':client.name if client else None,'status':inv.status,'risk_score':inv.risk_score,'finding':{'id':finding.id,'type':finding.finding_type,'statement':finding.statement,'confidence':finding.confidence,'evidence_refs':finding.evidence_refs} if finding else None,'configuration_comparison':comparison,'human_decision':{'decision':dec.decision,'reviewer':dec.reviewer,'reason':dec.reason,'authority_display_name':(dec.metadata_json or {}).get('authority_display_name'),'authority_role_title':(dec.metadata_json or {}).get('authority_role_title'),'decision_consistency':(dec.metadata_json or {}).get('decision_consistency')} if dec else None})
    return {'graph_run_id':graph_run_id,'results':out,'configuration_change_summary':build_configuration_change_summary(out)}

@router.get('/analysis-runs/{graph_run_id}/human-review')
def human_review(graph_run_id:str,db:Session=Depends(get_domain_db)):
    run=_run(db,graph_run_id);data=investigations(graph_run_id,db);pending=[x for x in data['results'] if not x['human_decision']]
    return {'graph_run_id':graph_run_id,'run_status':run.status,'pending_count':len(pending),'items':data['results'],'configuration_change_summary':data.get('configuration_change_summary')}
class ReviewDecision(BaseModel):
    investigation_id:str;decision:Literal['AFFECTED','NOT_AFFECTED','NEEDS_MORE_INVESTIGATION'];reason:str=Field(min_length=3,max_length=3000)
class ReviewRequest(BaseModel):
    reviewer:str=Field(min_length=2,max_length=180);decisions:list[ReviewDecision]
@router.post('/analysis-runs/{graph_run_id}/human-review/resume')
def human_resume(
    graph_run_id:str,
    payload:ReviewRequest,
    x_creed_principal: str | None = Header(default=None, alias="X-CREED-Principal"),
    db:Session=Depends(get_domain_db),
):
    authority = _authority_or_403(db, x_creed_principal, "can_submit_human_decision", payload.reviewer)
    from app.services.analysis_runs import langgraph_runtime_available, resume_analysis_run
    available, reason = langgraph_runtime_available()
    if not available: raise HTTPException(503,f"LANGGRAPH_RUNTIME_UNAVAILABLE: {reason}")
    run=_run(db,graph_run_id);invs=investigations_for_run(db,run.id);required={x.id for x in invs};supplied={x.investigation_id for x in payload.decisions}
    if required and supplied!=required:raise HTTPException(422,"COMPLETE_REVIEW_REQUIRED")
    consistency_checks=[]
    for item in payload.decisions:
        inv=db.get(Investigation,item.investigation_id)
        if not inv or inv.id not in required:raise HTTPException(422,"INVESTIGATION_NOT_IN_RUN")
        if inv.decisions:raise HTTPException(409,"HUMAN_DECISION_ALREADY_RECORDED")
        detail=db.scalar(select(InvestigationDetail).where(InvestigationDetail.investigation_id==inv.id))
        comparison=(detail.model_output_json or {}).get('configuration_comparison') if detail else None
        consistency=assess_human_decision_consistency(comparison,item.decision)
        if consistency and consistency.get('requires_explicit_rationale') and len(item.reason.strip()) < int(consistency.get('minimum_rationale_chars') or R9406_CONTRADICTION_RATIONALE_MIN_CHARS):
            raise HTTPException(422,"TECHNICAL_ADVISORY_CONTRADICTION_RATIONALE_REQUIRED")
        decision_meta={'graph_run_id':graph_run_id,'review_cycle':1,'finding_id':inv.findings[-1].id if inv.findings else None,'authority_id':authority.id,'authority_display_name':authority.display_name,'authority_role_title':authority.role_title}
        if consistency:
            decision_meta['decision_consistency']=consistency
            consistency_checks.append({'investigation_id':inv.id,**consistency})
        db.add(HumanDecision(investigation_id=inv.id,decision=item.decision,reviewer=authority.principal,reason=item.reason,metadata_json=decision_meta))
        inv.status='QUEUED' if item.decision=='NEEDS_MORE_INVESTIGATION' else 'COMPLETED'
    db.add(AuditEvent(actor=authority.principal,action='HUMAN_REVIEW_SUBMITTED',object_type='AgentRun',object_id=run.id,metadata_json={'authority_id':authority.id,'authority_display_name':authority.display_name,'authority_role_title':authority.role_title,'decisions':[x.model_dump() for x in payload.decisions],'decision_consistency':consistency_checks}))
    db.commit()
    try:
        resumed=resume_analysis_run(run_db_id=run.id,database_url=db.get_bind().url.render_as_string(hide_password=False),resume_payload={'reviewer':authority.principal,'decisions':[x.model_dump() for x in payload.decisions]})
    except Exception as exc:
        raise HTTPException(503,f"LANGGRAPH_RESUME_FAILED: {exc}") from exc
    return {'graph_run_id':graph_run_id,'status':resumed['status'],'decisions':[x.model_dump() for x in payload.decisions]}

class LearningCreate(BaseModel):
    new_version:str=Field(min_length=2,max_length=80);corrected_method:str=Field(min_length=10,max_length=10000);author:str=Field(min_length=2,max_length=180)
@router.get('/analysis-runs/{graph_run_id}/learning-readiness')
def learning_readiness_get(graph_run_id:str,db:Session=Depends(get_domain_db)):
    return learning_readiness(db,_run(db,graph_run_id))
@router.post('/analysis-runs/{graph_run_id}/learning-proposal')
def learning_create(
    graph_run_id:str,
    payload:LearningCreate,
    x_creed_principal: str | None = Header(default=None, alias="X-CREED-Principal"),
    db:Session=Depends(get_domain_db),
):
    authority = _authority_or_403(db, x_creed_principal, "can_submit_human_decision", payload.author)
    run = _run(db, graph_run_id)
    try:return create_learning_proposal(db,run,new_version=payload.new_version,corrected_method=payload.corrected_method,author=authority.principal)
    except Exception as e:_err(e)
@router.get('/analysis-runs/{graph_run_id}/learning-proposal')
def learning_get(graph_run_id:str,db:Session=Depends(get_domain_db)):
    run=_run(db,graph_run_id);p=db.scalar(
        select(LearningProposal)
        .join(LearningProposalDetail, LearningProposalDetail.learning_id == LearningProposal.id)
        .where(LearningProposalDetail.agent_run_id == run.id)
        .order_by(LearningProposal.created_at.desc())
        .limit(1)
    )
    return serialize_learning(db,p.id) if p else None
class LearningEdit(BaseModel):
    editor:str;summary:str|None=None;corrected_method:str|None=None;title:str|None=None;applicability:str|None=None;guardrails:list[str]|None=None;validation_steps:list[str]|None=None
@router.patch('/learning-proposals/{proposal_id}')
def learning_edit(proposal_id:str,payload:LearningEdit,db:Session=Depends(get_domain_db)):
    try:return edit_learning(db,proposal_id,**payload.model_dump())
    except Exception as e:_err(e)
class AdoptionScopeInput(BaseModel):
    mode:Literal['METHOD_CATALOG','CURRENT_REGISTERED_IMPLEMENTATIONS','SELECTED_IMPLEMENTATIONS']
    implementation_ids:list[str]=Field(default_factory=list)

class LearningDecision(BaseModel):
    reviewer:str;decision:Literal['APPROVE_LEARNING','REJECT_LEARNING'];reason:str=Field(min_length=3,max_length=3000);adoption_scope:AdoptionScopeInput|None=None
@router.post('/learning-proposals/{proposal_id}/decision')
def learning_decide(
    proposal_id:str,
    payload:LearningDecision,
    x_creed_principal: str | None = Header(default=None, alias="X-CREED-Principal"),
    db:Session=Depends(get_domain_db),
):
    authority = _authority_or_403(db, x_creed_principal, "can_approve_learning", payload.reviewer)
    try:
        return approve_learning(
            db,
            proposal_id,
            reviewer=authority.principal,
            decision=payload.decision,
            reason=payload.reason,
            adoption_scope=payload.adoption_scope.model_dump() if payload.adoption_scope else None,
        )
    except Exception as e:_err(e)
@router.get('/adoption-receipts/{receipt_id}')
def receipt(receipt_id:str,db:Session=Depends(get_domain_db)):
    try:return serialize_receipt(db,receipt_id)
    except Exception as e:_err(e)
@router.get('/adoption-receipts/{receipt_id}/verify')
def receipt_verify(receipt_id:str,db:Session=Depends(get_domain_db)):
    r=serialize_receipt(db,receipt_id);return {'valid':r['integrity']=='VALID','status':r['integrity'],'hash_algorithm':r['hash_algorithm'],'content_hash':r['content_hash']}

class RevokeRequest(BaseModel):
    source_issue_id:str
    evidence_document_ids:list[str]=Field(default_factory=list,max_length=50)
    reviewer:str
    reason:str=Field(min_length=3,max_length=5000)
@router.post('/method-versions/{version_id}/revoke')
def revoke(
    version_id:str,
    payload:RevokeRequest,
    x_creed_principal: str | None = Header(default=None, alias="X-CREED-Principal"),
    db:Session=Depends(get_domain_db),
):
    authority = _authority_or_403(db, x_creed_principal, "can_authorize_recall", payload.reviewer)
    try:
        return revoke_method(
            db,
            version_id,
            source_issue_id=payload.source_issue_id,
            evidence_document_ids=payload.evidence_document_ids,
            reviewer=authority.principal,
            reason=payload.reason,
        )
    except Exception as e:_err(e)
@router.get('/recalls')
def recalls(db:Session=Depends(get_domain_db)):
    return [serialize_recall(db,x.id) for x in db.scalars(select(RecallNotice).order_by(RecallNotice.created_at.desc())).all()]
@router.get('/recalls/{recall_id}')
def recall(recall_id:str,db:Session=Depends(get_domain_db)):
    try:return serialize_recall(db,recall_id)
    except Exception as e:_err(e)
@router.get('/recalls/{recall_id}/verify')
def recall_verify(recall_id:str,db:Session=Depends(get_domain_db)):
    r=serialize_recall(db,recall_id);return {'valid':r['integrity']=='VALID','status':r['integrity'],'hash_algorithm':'SHA-256','content_hash':r['content_hash']}
@router.get('/recalls/{recall_id}/change-radar')
def recall_radar(recall_id:str,db:Session=Depends(get_domain_db)):
    r=serialize_recall(db,recall_id);return {'recall_id':recall_id,'routed_implementations':len(r['cases']),'graph':r['graph']}

@router.get('/dashboard')
def dash(db:Session=Depends(get_domain_db)):return dashboard(db)
@router.get('/audit')
def audit(graph_run_id:str|None=Query(default=None),db:Session=Depends(get_domain_db)):return audit_trace(db,graph_run_id)
@router.get('/audit/timeline')
def audit_timeline(graph_run_id:str|None=Query(default=None),category:str|None=Query(default=None),db:Session=Depends(get_domain_db)):
    data=audit_trace(db,graph_run_id);data['timeline']=[x for x in data['timeline'] if not category or x['category']==category.upper()];return data
@router.get('/audit/runs/{graph_run_id}')
def audit_run(graph_run_id:str,db:Session=Depends(get_domain_db)):return audit_trace(db,graph_run_id)

@router.get('/resilience')
def resilience(db:Session=Depends(get_domain_db)):
    from app.core.ai_runtime import get_ollama_runtime
    try:qwen=get_ollama_runtime().runtime_snapshot(refresh=True)['status']
    except Exception:qwen='UNAVAILABLE'
    return {'module':'M19','version':'0.20.0','controls':{'prompt_injection_scan':'ENABLED','untrusted_prompt_boundaries':'ENABLED','evidence_validation':'ENABLED','contradictory_evidence':'ENABLED','issue_idempotency':'ENABLED','sse_resume':'LAST_EVENT_ID','database_pool_pre_ping':'ENABLED','qwen_structured_validation':'ENABLED','bounded_qwen_repair':'ONE_RETRY','no_fake_ai_fallback':'ENFORCED'},'qwen':qwen}

@router.get('/demo/status')
def demo_get(db:Session=Depends(get_domain_db)):return demo_status(db)

@router.get('/demo/readiness')
def demo_readiness_get(refresh_runtime:bool=Query(default=False),db:Session=Depends(get_domain_db)):
    return demo_readiness(db,refresh_runtime=refresh_runtime)

class ResetDemo(BaseModel):confirm:Literal['RESET CREED DEMO']
@router.post('/demo/reset')
def demo_reset(payload:ResetDemo,db:Session=Depends(get_domain_db)):
    if not get_settings().demo_mode_enabled:raise HTTPException(403,'DEMO_MODE_DISABLED')
    return reset_demo(db)
