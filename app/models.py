from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), nullable=False)  # admin, dos, teacher
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Class teacher assignments
    class_streams = relationship("TeacherStream", back_populates="teacher")
    subjects = relationship("TeacherSubject", back_populates="teacher")


class Stream(Base):
    __tablename__ = "streams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), unique=True, nullable=False)
    grade = Column(Integer, nullable=False)

    class_teachers = relationship("TeacherStream", back_populates="stream")


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20))
    is_core = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    teachers = relationship("TeacherSubject", back_populates="subject")


class TeacherStream(Base):
    """Class teacher assignment – only class teachers can access their streams."""
    __tablename__ = "teacher_streams"
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    stream_id = Column(Integer, ForeignKey("streams.id"))

    teacher = relationship("User", back_populates="class_streams")
    stream = relationship("Stream", back_populates="class_teachers")

    __table_args__ = (UniqueConstraint("teacher_id", "stream_id", name="uq_teacher_stream"),)


class TeacherSubject(Base):
    """Subjects a teacher is allowed to enter marks for."""
    __tablename__ = "teacher_subjects"
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))

    teacher = relationship("User", back_populates="subjects")
    subject = relationship("Subject", back_populates="teachers")

    __table_args__ = (UniqueConstraint("teacher_id", "subject_id", name="uq_teacher_subject"),)


class Learner(Base):
    __tablename__ = "learners"
    id = Column(Integer, primary_key=True, index=True)
    admission_no = Column(String(30), unique=True, index=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    gender = Column(String(10))
    stream_id = Column(Integer, ForeignKey("streams.id"))
    parent_name = Column(String(100))
    parent_phone = Column(String(20))
    view_code = Column(String(12), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    stream = relationship("Stream")
    marks = relationship("Mark", back_populates="learner")


class AcademicYear(Base):
    __tablename__ = "academic_years"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, unique=True, nullable=False)
    is_current = Column(Boolean, default=False)


class Term(Base):
    __tablename__ = "terms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), nullable=False)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"))
    is_current = Column(Boolean, default=False)

    academic_year = relationship("AcademicYear")


class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    assessment_type = Column(String(50))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    term_id = Column(Integer, ForeignKey("terms.id"))
    max_score = Column(Float, default=100.0)
    date = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    # Workflow: draft → submitted → countersigned
    status = Column(String(20), default="draft")  # draft, submitted, countersigned

    subject = relationship("Subject")
    term = relationship("Term")
    marks = relationship("Mark", back_populates="assessment")


class Mark(Base):
    __tablename__ = "marks"
    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"))
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    score = Column(Float, nullable=False)
    level = Column(String(10))
    comment = Column(Text)
    entered_by = Column(Integer, ForeignKey("users.id"))
    entered_at = Column(DateTime, default=datetime.utcnow)

    learner = relationship("Learner", back_populates="marks")
    assessment = relationship("Assessment", back_populates="marks")

    __table_args__ = (UniqueConstraint("learner_id", "assessment_id", name="unique_learner_assessment"),)


class ReportComment(Base):
    """Overall / class teacher / principal comments on a learner for a term."""
    __tablename__ = "report_comments"
    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"))
    term_id = Column(Integer, ForeignKey("terms.id"))
    class_teacher_comment = Column(Text)
    dos_comment = Column(Text)
    principal_comment = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("learner_id", "term_id", name="uq_learner_term_comment"),)
