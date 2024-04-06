from typing import Optional, List, Dict, Union
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict
from decimal import Decimal


class UploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    message: str
    full_path: str
    thumbnail_path: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ProcessingInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    message: str


class TokenData(BaseModel):
    email: str | None = None


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    phone: str
    role: str
    department: str | None


class Employee(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: str
    department: str
    sex: str
    age: int
    avatar: str
    quit_probability: float | None

class EmployeeList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employees: List[Employee]

class Period(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_date: str
    end_date: str

class Department(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

class DepartmentList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    departments: List[Department]

class PeriodList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    periods: List[Period]

class EmployeeStatistics(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    employee_name: str
    employee_email: str
    employee_department: str
    employee_quit_probability: float

class EmployeeStatisticsList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    statistics: List[EmployeeStatistics]


class EmployeeMetrica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    number_of_answered_emails: int
    number_of_sent_emails: int
    number_of_received_emails: int
    mean_number_of_recipients_in_one_email_for_user: float
    number_of_emails_read_after_x_minutes: int
    mean_number_of_days_between_receiving_emails_and_read: int
    number_of_sent_emails_outside_of_working_hours: int
    received_and_sent_emails_proportion_for_user: float
    mean_number_of_not_answered_questions_in_email: float
    mean_length_of_user_emails: float
    mean_answering_time_for_user: float
    number_of_passed_corporative_tests_or_courses_for_user: int
    number_of_unique_recipients_of_emails_for_user: int
    number_of_unique_departments_in_emails_for_user: int
    toxcity_in_sent_emails_for_user: str
    toxcity_in_received_emails_for_user: str
    emotions_in_sent_emails_for_user: str
    emotions_in_received_emails_for_user: str
    salary: int
    high_priority_emails_reply_delay: int
    medium_priority_emails_reply_delay: int
    low_priority_emails_reply_delay: int
    period: Period

class EmployeeMetricaList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metrics: List[EmployeeMetrica]
    periods: List[Period]