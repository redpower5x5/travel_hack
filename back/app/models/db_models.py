from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Enum,
    UniqueConstraint,
    TEXT,
    Numeric,
    Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class Role(enum.Enum):
    HR = "HR"
    admin = "admin"
    head_of_department = "head_of_department"

class Department(Base):
    __tablename__ = "department"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now())

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    phone = Column(String(50), nullable=False)
    hashed_password = Column(String(100), nullable=False)
    role = Column(Enum(Role), default=Role.HR)
    department_id = Column(Integer, ForeignKey("department.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    department = relationship("Department", backref="user")

class Employee(Base):
    __tablename__ = "employee"
    id = Column(Integer, primary_key=True)
    email = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    sex = Column(String(10), nullable=False)
    age = Column(Integer, nullable=False)
    department_id = Column(Integer, ForeignKey("department.id"))
    avatar = Column(TEXT, nullable=False)
    quit_probability = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    department = relationship("Department", backref="employee")

class ToxcicityLevel(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Emotion(enum.Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"

class Period(Base):
    __tablename__ = "period"
    id = Column(Integer, primary_key=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now())

class EmployeMetrica(Base):
    __tablename__ = "employee_metrica"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employee.id"))
    number_of_answered_emails = Column(Integer, nullable=False)
    number_of_sent_emails = Column(Integer, nullable=False)
    number_of_received_emails = Column(Integer, nullable=False)
    mean_number_of_recipients_in_one_email_for_user = Column(Numeric(10, 2), nullable=False)
    number_of_emails_read_after_x_minutes = Column(Integer, nullable=False)
    mean_number_of_days_between_receiving_emails_and_read = Column(Integer, nullable=False)
    number_of_sent_emails_outside_of_working_hours = Column(Integer, nullable=False)
    received_and_sent_emails_proportion_for_user = Column(Numeric(10, 2), nullable=False)
    mean_number_of_not_answered_questions_in_email = Column(Numeric(10, 2), nullable=False)
    mean_length_of_user_emails = Column(Numeric(10, 2), nullable=False)
    mean_answering_time_for_user = Column(Numeric(10, 2), nullable=False)
    number_of_passed_corporative_tests_or_courses_for_user = Column(Integer, nullable=False)
    number_of_unique_recipients_of_emails_for_user = Column(Integer, nullable=False)
    number_of_unique_departments_in_emails_for_user = Column(Integer, nullable=False)
    toxcity_in_sent_emails_for_user = Column(Enum(ToxcicityLevel), default=ToxcicityLevel.LOW)
    toxcity_in_received_emails_for_user = Column(Enum(ToxcicityLevel), default=ToxcicityLevel.LOW)
    emotions_in_sent_emails_for_user = Column(Enum(Emotion), default=Emotion.NEUTRAL)
    emotions_in_received_emails_for_user = Column(Enum(Emotion), default=Emotion.NEUTRAL)
    salary = Column(Integer, nullable=False)
    high_priority_emails_reply_delay = Column(Integer, nullable=False)
    medium_priority_emails_reply_delay = Column(Integer, nullable=False)
    low_priority_emails_reply_delay = Column(Integer, nullable=False)
    period_id = Column(Integer, ForeignKey("period.id"))
    created_at = Column(DateTime, default=datetime.now())
    period = relationship("Period", backref="employee_metrica")

