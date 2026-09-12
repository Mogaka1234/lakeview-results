from fastapi import FastAPI, Request, Depends, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
import secrets
import string
from pathlib import Path
from typing import Optional, List

from .database import engine, get_db, Base
from . import models, auth, grading, report_cards
from .auth import get_current_user, create_access_token, get_password_hash

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Lakeview Junior School Results System")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

from jinja2 import Environment, FileSystemLoader, select_autoescape
jinja_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    autoescape=select_autoescape(["html", "xml"]),
)

def render(request: Request, name: str, **ctx):
    template = jinja_env.get_template(name)
    ctx["request"] = request
    return HTMLResponse(template.render(**ctx))

SCHOOL_NAME = "Lakeview Junior School"
SCHOOL_DOMAIN = "results.lakeviewjunior.ac.ke"
SCHOOL_URL = "https://results.lakeviewjunior.ac.ke"


def generate_view_code(length=8):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ---------- Auth helpers ----------
async def require_staff(user=Depends(get_current_user)):
    if not user or user.role not in ("admin", "dos", "teacher"):
        raise HTTPException(status_code=403, detail="Staff access required")
    return user

async def require_admin_or_dos(user=Depends(get_current_user)):
    if not user or user.role not in ("admin", "dos"):
        raise HTTPException(status_code=403, detail="Admin or DOS access required")
    return user

async def require_admin(user=Depends(get_current_user)):
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def get_teacher_stream_ids(db: Session, user: models.User) -> List[int]:
    if user.role in ("admin", "dos"):
        return [s.id for s in db.query(models.Stream).all()]
    return [ts.stream_id for ts in db.query(models.TeacherStream).filter_by(teacher_id=user.id).all()]


def get_teacher_subject_ids(db: Session, user: models.User) -> List[int]:
    if user.role in ("admin", "dos"):
        return [s.id for s in db.query(models.Subject).filter_by(is_active=True).all()]
    return [ts.subject_id for ts in db.query(models.TeacherSubject).filter_by(teacher_id=user.id).all()]


def seed_initial_data(db: Session):
    if db.query(models.User).count() == 0:
        db.add(models.User(username="admin", hashed_password=get_password_hash("Lakeview@Admin2026"),
                           full_name="System Administrator", role="admin"))
        db.add(models.User(username="dos", hashed_password=get_password_hash("Lakeview@DOS2026"),
                           full_name="Director of Studies", role="dos"))
        db.add(models.User(username="teacher1", hashed_password=get_password_hash("Lakeview@Teach2026"),
                           full_name="Demo Class Teacher", role="teacher"))

    streams_data = [("7B", 7), ("7G", 7), ("8B", 8), ("8G", 8), ("8R", 8), ("9B", 9), ("9G", 9)]
    for name, grade in streams_data:
        if not db.query(models.Stream).filter_by(name=name).first():
            db.add(models.Stream(name=name, grade=grade))

    subjects = [
        ("English", "ENG"), ("Kiswahili", "KIS"), ("Mathematics", "MAT"),
        ("Integrated Science", "ISC"), ("Pre-Technical Studies", "PTS"),
        ("Social Studies", "SST"), ("Religious Education", "RE"),
        ("Agriculture", "AGR"), ("Creative Arts and Sports", "CAS"),
    ]
    for name, code in subjects:
        if not db.query(models.Subject).filter_by(name=name).first():
            db.add(models.Subject(name=name, code=code, is_core=True))

    year = datetime.now().year
    ay = db.query(models.AcademicYear).filter_by(year=year).first()
    if not ay:
        ay = models.AcademicYear(year=year, is_current=True)
        db.add(ay)
        db.flush()
        for tname in ["Term 1", "Term 2", "Term 3"]:
            db.add(models.Term(name=tname, academic_year_id=ay.id, is_current=(tname == "Term 1")))
    db.commit()


@app.on_event("startup")
def startup():
    db = next(get_db())
    seed_initial_data(db)
    db.close()


# ========== PUBLIC / PARENT ==========
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user=Depends(get_current_user)):
    return render(request, "home.html", user=user, school=SCHOOL_NAME)


@app.get("/parent", response_class=HTMLResponse)
async def parent_view(request: Request):
    return render(request, "parent_login.html", school=SCHOOL_NAME)


@app.post("/parent/view")
async def parent_view_results(request: Request, view_code: str = Form(...), db: Session = Depends(get_db)):
    learner = db.query(models.Learner).filter(
        models.Learner.view_code == view_code.upper().strip(),
        models.Learner.is_active == True,
    ).first()
    if not learner:
        return render(request, "parent_login.html", school=SCHOOL_NAME,
                      error="Invalid view code. Please check and try again.")
    marks = (
        db.query(models.Mark)
        .join(models.Assessment)
        .options(joinedload(models.Mark.assessment).joinedload(models.Assessment.subject),
                 joinedload(models.Mark.assessment).joinedload(models.Assessment.term))
        .filter(models.Mark.learner_id == learner.id)
        .order_by(models.Assessment.term_id, models.Assessment.subject_id)
        .all()
    )
    return render(request, "parent_results.html", school=SCHOOL_NAME, learner=learner,
                  marks=marks, get_level_description=grading.get_level_description)


# ========== AUTH ==========
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return render(request, "login.html", school=SCHOOL_NAME)


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...),
                db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, username, password)
    if not user:
        return render(request, "login.html", school=SCHOOL_NAME, error="Invalid username or password")
    token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=60*60*12)
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


# ========== DASHBOARD ==========
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(require_staff), db: Session = Depends(get_db)):
    stream_ids = get_teacher_stream_ids(db, user)
    learners_count = db.query(models.Learner).filter(
        models.Learner.is_active == True,
        models.Learner.stream_id.in_(stream_ids) if stream_ids else True
    ).count()
    subjects_count = len(get_teacher_subject_ids(db, user))
    return render(request, "dashboard.html", user=user, school=SCHOOL_NAME,
                  learners_count=learners_count, subjects_count=subjects_count)


# ========== LEARNERS ==========
@app.get("/learners", response_class=HTMLResponse)
async def list_learners(request: Request, user=Depends(require_staff), db: Session = Depends(get_db),
                        stream_id: Optional[int] = Query(None)):
    stream_ids = get_teacher_stream_ids(db, user)
    q = db.query(models.Learner).filter(models.Learner.is_active == True)
    if stream_id and stream_id in stream_ids:
        q = q.filter(models.Learner.stream_id == stream_id)
    elif stream_ids:
        q = q.filter(models.Learner.stream_id.in_(stream_ids))
    learners = q.order_by(models.Learner.admission_no).all()
    streams = db.query(models.Stream).filter(models.Stream.id.in_(stream_ids)).all() if stream_ids else []
    return render(request, "learners.html", user=user, school=SCHOOL_NAME,
                  learners=learners, streams=streams, selected_stream=stream_id)


@app.post("/learners/add")
async def add_learner(
    request: Request,
    admission_no: str = Form(...), first_name: str = Form(...), last_name: str = Form(...),
    gender: str = Form(""), stream_id: int = Form(...),
    parent_name: str = Form(""), parent_phone: str = Form(""),
    user=Depends(require_staff), db: Session = Depends(get_db),
):
    allowed = get_teacher_stream_ids(db, user)
    if stream_id not in allowed and user.role not in ("admin", "dos"):
        raise HTTPException(403, "You can only register learners in your assigned streams")
    if db.query(models.Learner).filter_by(admission_no=admission_no.strip()).first():
        raise HTTPException(400, "Admission number already exists")
    view_code = generate_view_code()
    while db.query(models.Learner).filter_by(view_code=view_code).first():
        view_code = generate_view_code()
    db.add(models.Learner(
        admission_no=admission_no.strip(), first_name=first_name.strip(), last_name=last_name.strip(),
        gender=gender, stream_id=stream_id, parent_name=parent_name.strip(),
        parent_phone=parent_phone.strip(), view_code=view_code,
    ))
    db.commit()
    return RedirectResponse(url="/learners", status_code=303)


# ========== SUBJECTS (Admin) ==========
@app.get("/subjects", response_class=HTMLResponse)
async def list_subjects(request: Request, user=Depends(require_admin), db: Session = Depends(get_db)):
    subjects = db.query(models.Subject).order_by(models.Subject.name).all()
    return render(request, "subjects.html", user=user, school=SCHOOL_NAME, subjects=subjects)


@app.post("/subjects/add")
async def add_subject(name: str = Form(...), code: str = Form(""), user=Depends(require_admin),
                      db: Session = Depends(get_db)):
    if db.query(models.Subject).filter_by(name=name.strip()).first():
        raise HTTPException(400, "Subject already exists")
    db.add(models.Subject(name=name.strip(), code=code.strip().upper() or None))
    db.commit()
    return RedirectResponse(url="/subjects", status_code=303)


@app.post("/subjects/{subject_id}/toggle")
async def toggle_subject(subject_id: int, user=Depends(require_admin), db: Session = Depends(get_db)):
    subj = db.query(models.Subject).get(subject_id)
    if subj:
        subj.is_active = not subj.is_active
        db.commit()
    return RedirectResponse(url="/subjects", status_code=303)


# ========== TEACHER ASSIGNMENTS (Admin) ==========
@app.get("/assignments", response_class=HTMLResponse)
async def assignments_page(request: Request, user=Depends(require_admin), db: Session = Depends(get_db)):
    teachers = db.query(models.User).filter(models.User.role == "teacher", models.User.is_active == True).all()
    streams = db.query(models.Stream).all()
    subjects = db.query(models.Subject).filter_by(is_active=True).all()
    ts = db.query(models.TeacherStream).all()
    tsub = db.query(models.TeacherSubject).all()
    return render(request, "assignments.html", user=user, school=SCHOOL_NAME,
                  teachers=teachers, streams=streams, subjects=subjects,
                  teacher_streams=ts, teacher_subjects=tsub)


@app.post("/assignments/stream")
async def assign_stream(teacher_id: int = Form(...), stream_id: int = Form(...),
                        user=Depends(require_admin), db: Session = Depends(get_db)):
    if not db.query(models.TeacherStream).filter_by(teacher_id=teacher_id, stream_id=stream_id).first():
        db.add(models.TeacherStream(teacher_id=teacher_id, stream_id=stream_id))
        db.commit()
    return RedirectResponse(url="/assignments", status_code=303)


@app.post("/assignments/subject")
async def assign_subject(teacher_id: int = Form(...), subject_id: int = Form(...),
                         user=Depends(require_admin), db: Session = Depends(get_db)):
    if not db.query(models.TeacherSubject).filter_by(teacher_id=teacher_id, subject_id=subject_id).first():
        db.add(models.TeacherSubject(teacher_id=teacher_id, subject_id=subject_id))
        db.commit()
    return RedirectResponse(url="/assignments", status_code=303)


@app.post("/assignments/stream/remove/{id}")
async def remove_stream_assign(id: int, user=Depends(require_admin), db: Session = Depends(get_db)):
    row = db.query(models.TeacherStream).get(id)
    if row:
        db.delete(row)
        db.commit()
    return RedirectResponse(url="/assignments", status_code=303)


@app.post("/assignments/subject/remove/{id}")
async def remove_subject_assign(id: int, user=Depends(require_admin), db: Session = Depends(get_db)):
    row = db.query(models.TeacherSubject).get(id)
    if row:
        db.delete(row)
        db.commit()
    return RedirectResponse(url="/assignments", status_code=303)


# ========== ASSESSMENTS ==========
@app.get("/assessments", response_class=HTMLResponse)
async def list_assessments(request: Request, user=Depends(require_staff), db: Session = Depends(get_db)):
    subject_ids = get_teacher_subject_ids(db, user)
    assessments = (
        db.query(models.Assessment)
        .filter(models.Assessment.subject_id.in_(subject_ids) if subject_ids else True)
        .order_by(models.Assessment.id.desc())
        .limit(80)
        .all()
    )
    subjects = db.query(models.Subject).filter(models.Subject.id.in_(subject_ids)).all() if subject_ids else []
    terms = db.query(models.Term).all()
    return render(request, "assessments.html", user=user, school=SCHOOL_NAME,
                  assessments=assessments, subjects=subjects, terms=terms)


@app.post("/assessments/add")
async def add_assessment(
    name: str = Form(...), assessment_type: str = Form("CAT"),
    subject_id: int = Form(...), term_id: int = Form(...), max_score: float = Form(100.0),
    user=Depends(require_staff), db: Session = Depends(get_db),
):
    allowed_subjects = get_teacher_subject_ids(db, user)
    if subject_id not in allowed_subjects:
        raise HTTPException(403, "You are not assigned this subject")
    a = models.Assessment(
        name=name.strip(), assessment_type=assessment_type, subject_id=subject_id,
        term_id=term_id, max_score=max_score, created_by=user.id, status="draft",
    )
    db.add(a)
    db.commit()
    return RedirectResponse(url="/assessments", status_code=303)


# ========== MARKS ENTRY (with stream filter) ==========
@app.get("/marks/enter/{assessment_id}", response_class=HTMLResponse)
async def enter_marks_page(
    assessment_id: int, request: Request, user=Depends(require_staff),
    db: Session = Depends(get_db), stream_id: Optional[int] = Query(None),
):
    assessment = db.query(models.Assessment).options(
        joinedload(models.Assessment.subject), joinedload(models.Assessment.term)
    ).get(assessment_id)
    if not assessment:
        raise HTTPException(404)
    allowed_subjects = get_teacher_subject_ids(db, user)
    if assessment.subject_id not in allowed_subjects:
        raise HTTPException(403, "You are not assigned this subject")

    stream_ids = get_teacher_stream_ids(db, user)
    streams = db.query(models.Stream).filter(models.Stream.id.in_(stream_ids)).all() if stream_ids else []

    q = db.query(models.Learner).filter(models.Learner.is_active == True)
    if stream_id and stream_id in stream_ids:
        q = q.filter(models.Learner.stream_id == stream_id)
    elif stream_ids:
        q = q.filter(models.Learner.stream_id.in_(stream_ids))
    learners = q.order_by(models.Learner.admission_no).all()

    existing = {m.learner_id: m for m in db.query(models.Mark).filter_by(assessment_id=assessment_id).all()}
    return render(request, "enter_marks.html", user=user, school=SCHOOL_NAME,
                  assessment=assessment, learners=learners, existing=existing,
                  streams=streams, selected_stream=stream_id,
                  get_level=grading.get_performance_level)


@app.post("/marks/save/{assessment_id}")
async def save_marks(assessment_id: int, request: Request, user=Depends(require_staff),
                     db: Session = Depends(get_db)):
    form = await request.form()
    assessment = db.query(models.Assessment).get(assessment_id)
    if not assessment:
        raise HTTPException(404)
    allowed_subjects = get_teacher_subject_ids(db, user)
    if assessment.subject_id not in allowed_subjects:
        raise HTTPException(403, "You are not assigned this subject")
    if assessment.status == "countersigned":
        raise HTTPException(403, "This assessment has been countersigned and is locked")

    for key, value in form.items():
        if key.startswith("score_") and value.strip():
            learner_id = int(key.split("_")[1])
            try:
                score = float(value)
                if score < 0 or score > assessment.max_score:
                    continue
                pct = (score / assessment.max_score) * 100 if assessment.max_score != 100 else score
                level = grading.get_performance_level(pct)
                comment = form.get(f"comment_{learner_id}", "").strip() or None
                existing = db.query(models.Mark).filter_by(
                    learner_id=learner_id, assessment_id=assessment_id
                ).first()
                if existing:
                    existing.score = pct
                    existing.level = level
                    existing.comment = comment
                    existing.entered_by = user.id
                    existing.entered_at = datetime.utcnow()
                else:
                    db.add(models.Mark(
                        learner_id=learner_id, assessment_id=assessment_id,
                        score=pct, level=level, comment=comment, entered_by=user.id,
                    ))
            except ValueError:
                continue
    db.commit()
    stream = form.get("stream_id")
    url = f"/marks/enter/{assessment_id}"
    if stream:
        url += f"?stream_id={stream}"
    return RedirectResponse(url=url, status_code=303)


@app.post("/assessments/{assessment_id}/submit")
async def submit_assessment(assessment_id: int, user=Depends(require_staff), db: Session = Depends(get_db)):
    a = db.query(models.Assessment).get(assessment_id)
    if not a:
        raise HTTPException(404)
    allowed = get_teacher_subject_ids(db, user)
    if a.subject_id not in allowed and user.role not in ("admin", "dos"):
        raise HTTPException(403)
    if a.status == "draft":
        a.status = "submitted"
        db.commit()
    return RedirectResponse(url="/assessments", status_code=303)


@app.post("/assessments/{assessment_id}/countersign")
async def countersign_assessment(assessment_id: int, user=Depends(require_admin_or_dos),
                                 db: Session = Depends(get_db)):
    a = db.query(models.Assessment).get(assessment_id)
    if not a:
        raise HTTPException(404)
    if a.status == "submitted":
        a.status = "countersigned"
        db.commit()
    return RedirectResponse(url="/assessments", status_code=303)


# ========== REPORTS (Admin + DOS only for print) ==========
@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request, user=Depends(require_staff), db: Session = Depends(get_db)):
    streams = db.query(models.Stream).all()
    terms = db.query(models.Term).all()
    can_print = user.role in ("admin", "dos")
    return render(request, "reports.html", user=user, school=SCHOOL_NAME,
                  streams=streams, terms=terms, can_print=can_print)


@app.get("/reports/generate")
async def generate_report(
    request: Request,
    learner_id: int = Query(...),
    term_id: int = Query(...),
    user=Depends(require_admin_or_dos),
    db: Session = Depends(get_db),
):
    learner = db.query(models.Learner).options(joinedload(models.Learner.stream)).get(learner_id)
    term = db.query(models.Term).options(joinedload(models.Term.academic_year)).get(term_id)
    if not learner or not term:
        raise HTTPException(404)

    # Collect latest mark per subject for this term
    marks = (
        db.query(models.Mark)
        .join(models.Assessment)
        .options(joinedload(models.Mark.assessment).joinedload(models.Assessment.subject))
        .filter(models.Mark.learner_id == learner_id, models.Assessment.term_id == term_id)
        .all()
    )
    # Prefer highest assessment or just take all unique subjects (last one wins)
    by_subject = {}
    for m in marks:
        if m.assessment and m.assessment.subject:
            by_subject[m.assessment.subject.name] = {
                "subject": m.assessment.subject.name,
                "score": m.score,
                "level": m.level,
                "comment": m.comment or "",
            }
    subject_results = list(by_subject.values())
    if not subject_results:
        raise HTTPException(400, "No marks found for this learner in the selected term")

    avg = sum(r["score"] for r in subject_results) / len(subject_results)
    overall_level = grading.get_performance_level(avg)

    # Comments
    rc = db.query(models.ReportComment).filter_by(learner_id=learner_id, term_id=term_id).first()
    class_c = rc.class_teacher_comment if rc else ""
    dos_c = rc.dos_comment if rc else ""
    prin_c = rc.principal_comment if rc else ""

    pdf_bytes = report_cards.generate_report_card(
        learner=learner, term=term, subject_results=subject_results,
        class_teacher_comment=class_c, dos_comment=dos_c, principal_comment=prin_c,
        overall_level=overall_level, overall_average=avg,
    )
    filename = f"Report_{learner.admission_no}_{term.name.replace(' ', '')}_{datetime.now().year}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@app.get("/reports/class")
async def class_reports_page(
    request: Request,
    stream_id: int = Query(...),
    term_id: int = Query(...),
    user=Depends(require_admin_or_dos),
    db: Session = Depends(get_db),
):
    stream = db.query(models.Stream).get(stream_id)
    term = db.query(models.Term).get(term_id)
    learners = db.query(models.Learner).filter_by(stream_id=stream_id, is_active=True).order_by(
        models.Learner.admission_no
    ).all()
    return render(request, "class_reports.html", user=user, school=SCHOOL_NAME,
                  stream=stream, term=term, learners=learners)


# Simple comment editor for class teacher / DOS
@app.get("/comments/{learner_id}/{term_id}", response_class=HTMLResponse)
async def edit_comments(learner_id: int, term_id: int, request: Request,
                        user=Depends(require_staff), db: Session = Depends(get_db)):
    learner = db.query(models.Learner).get(learner_id)
    term = db.query(models.Term).get(term_id)
    rc = db.query(models.ReportComment).filter_by(learner_id=learner_id, term_id=term_id).first()
    return render(request, "comments.html", user=user, school=SCHOOL_NAME,
                  learner=learner, term=term, rc=rc)


@app.post("/comments/{learner_id}/{term_id}")
async def save_comments(
    learner_id: int, term_id: int, request: Request,
    class_teacher_comment: str = Form(""), dos_comment: str = Form(""),
    principal_comment: str = Form(""),
    user=Depends(require_staff), db: Session = Depends(get_db),
):
    rc = db.query(models.ReportComment).filter_by(learner_id=learner_id, term_id=term_id).first()
    if not rc:
        rc = models.ReportComment(learner_id=learner_id, term_id=term_id)
        db.add(rc)
    if user.role in ("teacher", "admin", "dos"):
        rc.class_teacher_comment = class_teacher_comment.strip()
    if user.role in ("dos", "admin"):
        rc.dos_comment = dos_comment.strip()
    if user.role == "admin":
        rc.principal_comment = principal_comment.strip()
    rc.updated_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(url=f"/comments/{learner_id}/{term_id}", status_code=303)
