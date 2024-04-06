from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from datetime import datetime

from typing import Union

from app.models import db_models, models
from app.schemas import response_schemas, request_schemas
from app.config import log
from app.utils.token import get_password_hash
from app.utils.next_week import get_next_week_dates
from app.ml.model_processor import predict_quit_probability
import os

from typing import List

import pandas as pd


def get_user(db: Session, email: Union[str, None]) -> Union[models.UserInDB, None]:
    try:
        user = (
            db.query(db_models.User)
            .filter(
                db_models.User.email == email,
            )
            .one()
        )
        user = models.UserInDB(
            id=user.id,
            email=user.email,
            username=user.username,
            phone=user.phone,
            hashed_password=user.hashed_password,
            role=user.role,
            department=user.department.name if user.department is not None else None,
        )
        return user
    except NoResultFound:
        return None
def check_if_user_admin(db: Session, user: response_schemas.User) -> bool:
    try:
        result = (
            db.query(db_models.User)
            .filter_by(
                id=user.id,
                role=db_models.Role.admin,
            ).first()
        )
        return result is not None
    except NoResultFound:
        return False

def create_user(db: Session, user: request_schemas.UserCreate) -> response_schemas.User:
    db_user = db_models.User(
        email=user.email,
        phone=user.phone,
        username=user.username,
        hashed_password=get_password_hash(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    db_user = response_schemas.User.model_validate(db_user)

    log.info(f"Created user: {db_user}")
    return db_user

def user_update(db: Session,
                user: request_schemas.UserUpdate,
                current_user: response_schemas.User
                ) -> Union[response_schemas.User, None]:
    try:
        db_user = (
            db.query(db_models.User)
            .filter(
                db_models.User.id == current_user.id,
            )
            .one()
        )
        if user.email:
            db_user.email = user.email
        if user.phone:
            db_user.phone = user.phone
        if user.username:
            db_user.username = user.username
        if user.password:
            db_user.hashed_password = get_password_hash(user.password)
        db.commit()
        db.refresh(db_user)


        db_user = response_schemas.User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            phone=db_user.phone,
            role=db_user.role,
            department=db_user.department.name if db_user.department is not None else None,
        )

        log.info(f"Updated user {db_user}")
        return db_user

    except NoResultFound:
        return None

def get_all_periods(db: Session, user: response_schemas.User) -> Union[response_schemas.PeriodList, None]:
    try:
        periods = (
            db.query(db_models.Period)
            .order_by(db_models.Period.start_date)
            .all()
        )
        periods = [response_schemas.Period(
            id=period.id,
            start_date=period.start_date.strftime("%Y-%m-%d"),
            end_date=period.end_date.strftime("%Y-%m-%d"),
        ) for period in periods]
        return response_schemas.PeriodList(periods=periods)
    except NoResultFound:
        return None

def get_all_departments(db: Session, user: response_schemas.User) -> Union[response_schemas.DepartmentList, None]:
    try:
        if user.department is not None:
            departments = (
                db.query(db_models.Department)
                .filter(
                    db_models.Department.name == user.department,
                )
                .all()
            )
        else:
            departments = (
                db.query(db_models.Department)
                .all()
            )
        departments = [response_schemas.Department(
            id=department.id,
            name=department.name,
        ) for department in departments]
        return response_schemas.DepartmentList(departments=departments)
    except NoResultFound:
        return None

def get_employee(db: Session,
                 id: int,
                 user: response_schemas.User
                 ) -> Union[response_schemas.Employee, None]:
    try:
        employee = (
            db.query(db_models.Employee)
            .filter(
                db_models.Employee.id == id,
            )
            .one()
        )
        employee = response_schemas.Employee(
            id=employee.id,
            name=employee.name,
            email=employee.email,
            phone=employee.phone,
            department=employee.department.name,
            sex=employee.sex,
            age=employee.age,
            avatar=employee.avatar,
            quit_probability=employee.quit_probability,
        )
        return employee
    except NoResultFound:
        return None

def get_user_statistics(db: Session,
                        department_ids: List[int],
                        date_from: str,
                        date_to: str,
                        user: response_schemas.User
                        ) -> Union[response_schemas.EmployeeStatisticsList, None]:
    try:
        query = db.query(db_models.Employee)
        if department_ids is not None:
            # force user to see only his department statistics
            if user.department is not None:
                department_ids = (
                    db.query(db_models.Department.id)
                    .filter(
                        db_models.Department.name == user.department,
                    )
                    .all()
                )
                department_ids = [department_id[0] for department_id in department_ids]
            query = query.filter(
                db_models.Employee.department_id.in_(department_ids),
            )

        # force user to see only his department statistics
        if user.department is not None:
            department_ids = (
                db.query(db_models.Department.id)
                .filter(
                    db_models.Department.name == user.department,
                )
                .all()
            )
            department_ids = [department_id[0] for department_id in department_ids]
            query = query.filter(
                db_models.Employee.department_id.in_(department_ids),
            )
        result = query.order_by(db_models.Employee.quit_probability.desc()).all()
        statistics = []
        for employee in result:
            statistics.append(response_schemas.EmployeeStatistics(
                employee_id=employee.id,
                employee_name=employee.name,
                employee_email=employee.email,
                employee_department=employee.department.name,
                employee_quit_probability=employee.quit_probability,
            ))
        return response_schemas.EmployeeStatisticsList(statistics=statistics)
    except NoResultFound:
        return None

def get_all_employees(db: Session,
                      user: response_schemas.User
                      ) -> Union[response_schemas.EmployeeList, None]:
    try:
        employees = (
            db.query(db_models.Employee)
            .all()
        )
        employees_list = []
        for employee in employees:
            model = response_schemas.Employee(
                id=employee.id,
                name=employee.name,
                email=employee.email,
                phone=employee.phone,
                department=employee.department.name,
                sex=employee.sex,
                age=employee.age,
                avatar=employee.avatar,
            )
            employees_list.append(model)
        return response_schemas.EmployeeList(employees=employees_list)
    except NoResultFound:
        return None

def upload_employeelist(db: Session,
                           file_path: str,
                           current_user: response_schemas.User
                           ) -> None:
    try:
        df = pd.read_csv(file_path, sep=';')
        for index, row in df.iterrows():
            # check if employee exists
            employee = (
                db.query(db_models.Employee)
                .filter(
                    db_models.Employee.email == row["email"],
                )
                .first()
            )
            if employee is None:
                # create employee
                employee = db_models.Employee(
                    email=row["email"],
                    name=row["name"],
                    phone=row["phone"],
                    sex=row['sex'],
                    age=row['age'],
                    avatar=row['avatar'],
                )
                # find department_id by name
                department = (
                    db.query(db_models.Department)
                    .filter(
                        db_models.Department.name == row["department"],
                    )
                    .first()
                )
                if department is not None:
                    employee.department_id = department.id
                else:
                    # create department
                    department = db_models.Department(
                        name=row["department"],
                    )
                    db.add(department)
                    db.commit()
                    db.refresh(department)
                    employee.department_id = department.id
                db.add(employee)
                db.commit()
                db.refresh(employee)
            else:
                log.info(f"Employee {employee} already exists")
    except NoResultFound:
        return None

def set_employee_quit_probability(db: Session,
                                  df: pd.DataFrame,
                                  ) -> None:
    try:
        for index, row in df.iterrows():
            # check if employee exists
            employee = (
                db.query(db_models.Employee)
                .filter(
                    db_models.Employee.email == row["Почтовый адрес"],
                )
                .first()
            )
            if employee is None:
                log.info(f"Employee {row['Почтовый адрес']} does not exist")
                continue
            # update employee quit probability
            employee.quit_probability = row["Вероятность увольнения"]
            db.commit()
            db.refresh(employee)
    except NoResultFound:
        return None

def upload_employe_metrics(db: Session,
                            file_path: str,
                            current_user: response_schemas.User
                            ) -> None:
    #  columns :
    #  ['Почтовый адрес', 'Колличество ответов',
    #    'Количество отправленных писем', 'Количество полученных писем',
    #    'Среднее количество получателей в письме',
    #    'Количество писем, прочитанных через 60 минут после получения',
    #    'Среднее количество дней между получением и прочтением письма',
    #    'Количество писем, отправленных в нерабочее время',
    #    'Соотношение полученных и отправленных писем',
    #    'Количество неотвеченных вопросов в письмах', 'Средняя длина письма',
    #    'Среднее время ответа на письмо',
    #    'Количество пройденных корпоративных тестов и курсов',
    #    'Количество уникальных получателей писем',
    #    'Количество уникальных отделов в письмах',
    #    'Средняя токсичность отправленных писем',
    #    'Средняя токсичность полученных писем',
    #    'Средняя эмоциональность отправленных писем',
    #    'Средняя эмоциональность полученных писем', 'Зарплата',
    #    'высокая срочность', 'средняя срочность', 'не срочно']
    try:
        df = pd.read_csv(file_path, sep=';')
        if df.empty:
            log.info(f"File {file_path} is empty")
            return None
        period = None
        # check if any period exists
        period = (
                db.query(db_models.Period).first()
        )
        if period is None:
            log.info(f"No Period exists. Generating first period 2023-12-04 - 2023-12-10")
            period = db_models.Period(
                start_date=datetime.strptime('2023-12-04', '%Y-%m-%d'),
                end_date=datetime.strptime('2023-12-10', '%Y-%m-%d'),
            )
        else:
            # there are periods, get latest one
            period = (
                db.query(db_models.Period)
                .order_by(db_models.Period.start_date.desc())
                .first()
            )
            # gen new period
            new_start, new_end = get_next_week_dates(period.start_date)
            period = db_models.Period(
                start_date=new_start,
                end_date=new_end,
            )
        db.add(period)
        db.commit()
        db.refresh(period)
        for index, row in df.iterrows():
            # check if employee exists
            employee = (
                db.query(db_models.Employee)
                .filter(
                    db_models.Employee.email == row["Почтовый адрес"],
                )
                .first()
            )
            if employee is None:
                    log.info(f"Employee {row['Почтовый адрес']} does not exist")
                    continue
            # create employee metrica
            employee_metrica = db_models.EmployeMetrica(
                employee_id=employee.id,
                number_of_answered_emails=row["Колличество ответов"],
                number_of_sent_emails=row["Количество отправленных писем"],
                number_of_received_emails=row["Количество полученных писем"],
                mean_number_of_recipients_in_one_email_for_user=row["Среднее количество получателей в письме"],
                number_of_emails_read_after_x_minutes=row["Количество писем, прочитанных через 60 минут после получения"],
                mean_number_of_days_between_receiving_emails_and_read=row["Среднее количество дней между получением и прочтением письма"],
                number_of_sent_emails_outside_of_working_hours=row["Количество писем, отправленных в нерабочее время"],
                received_and_sent_emails_proportion_for_user=row["Соотношение полученных и отправленных писем"],
                mean_number_of_not_answered_questions_in_email=row["Количество неотвеченных вопросов в письмах"],
                mean_length_of_user_emails=row["Средняя длина письма"],
                mean_answering_time_for_user=row["Среднее время ответа на письмо"],
                number_of_passed_corporative_tests_or_courses_for_user=row["Количество пройденных корпоративных тестов и курсов"],
                number_of_unique_recipients_of_emails_for_user=row["Количество уникальных получателей писем"],
                number_of_unique_departments_in_emails_for_user=row["Количество уникальных отделов в письмах"],
                toxcity_in_sent_emails_for_user=row["Средняя токсичность отправленных писем"],
                toxcity_in_received_emails_for_user=row["Средняя токсичность полученных писем"],
                emotions_in_sent_emails_for_user=row["Средняя эмоциональность отправленных писем"],
                emotions_in_received_emails_for_user=row["Средняя эмоциональность полученных писем"],
                salary=row["Зарплата"],
                high_priority_emails_reply_delay=row["высокая срочность"],
                medium_priority_emails_reply_delay=row["средняя срочность"],
                low_priority_emails_reply_delay=row["не срочно"],
                period_id=period.id,
            )
            db.add(employee_metrica)
            db.commit()
            db.refresh(employee_metrica)
        #run ml to predict quit probability on each employee metrica in period
        prediction_df = predict_quit_probability(df)
        set_employee_quit_probability(db, prediction_df)
    except NoResultFound:
        return None

def get_employee_metrics(db: Session,
                         id: int,
                         user: response_schemas.User
                         ) -> Union[response_schemas.EmployeeMetricaList, None]:
    try:
        metrics = (
            db.query(db_models.EmployeMetrica)
            .filter(
                db_models.EmployeMetrica.employee_id == id,
            ).order_by(db_models.EmployeMetrica.period_id.asc())
            .all()
        )
        metrics_list = []
        periods = []
        for metric in metrics:
            period = response_schemas.Period(
                    id=metric.period.id,
                    start_date=metric.period.start_date.strftime("%Y-%m-%d"),
                    end_date=metric.period.end_date.strftime("%Y-%m-%d"),
                )
            periods.append(period)
            model = response_schemas.EmployeeMetrica(
                id=metric.id,
                employee_id=metric.employee_id,
                number_of_answered_emails=metric.number_of_answered_emails,
                number_of_sent_emails=metric.number_of_sent_emails,
                number_of_received_emails=metric.number_of_received_emails,
                mean_number_of_recipients_in_one_email_for_user=metric.mean_number_of_recipients_in_one_email_for_user,
                number_of_emails_read_after_x_minutes=metric.number_of_emails_read_after_x_minutes,
                mean_number_of_days_between_receiving_emails_and_read=metric.mean_number_of_days_between_receiving_emails_and_read,
                number_of_sent_emails_outside_of_working_hours=metric.number_of_sent_emails_outside_of_working_hours,
                received_and_sent_emails_proportion_for_user=metric.received_and_sent_emails_proportion_for_user,
                mean_number_of_not_answered_questions_in_email=metric.mean_number_of_not_answered_questions_in_email,
                mean_length_of_user_emails=metric.mean_length_of_user_emails,
                mean_answering_time_for_user=metric.mean_answering_time_for_user,
                number_of_passed_corporative_tests_or_courses_for_user=metric.number_of_passed_corporative_tests_or_courses_for_user,
                number_of_unique_recipients_of_emails_for_user=metric.number_of_unique_recipients_of_emails_for_user,
                number_of_unique_departments_in_emails_for_user=metric.number_of_unique_departments_in_emails_for_user,
                toxcity_in_sent_emails_for_user=metric.toxcity_in_sent_emails_for_user,
                toxcity_in_received_emails_for_user=metric.toxcity_in_received_emails_for_user,
                emotions_in_sent_emails_for_user=metric.emotions_in_sent_emails_for_user,
                emotions_in_received_emails_for_user=metric.emotions_in_received_emails_for_user,
                salary=metric.salary,
                high_priority_emails_reply_delay=metric.high_priority_emails_reply_delay,
                medium_priority_emails_reply_delay=metric.medium_priority_emails_reply_delay,
                low_priority_emails_reply_delay=metric.low_priority_emails_reply_delay,
                period=period,
            )
            metrics_list.append(model)
        return response_schemas.EmployeeMetricaList(metrics=metrics_list, periods=periods)
    except NoResultFound:
        return None

def export_employee_metrics_excel_file(db: Session,
                                       id: int,
                                       user: response_schemas.User
                                       ) -> Union[str, None]:  # file_path
    try:
        metrics = (
            db.query(db_models.EmployeMetrica)
            .filter(
                db_models.EmployeMetrica.employee_id == id,
            ).order_by(db_models.EmployeMetrica.period_id.asc())
            .all()
        )
        metrics_list = []
        periods = []
        for metric in metrics:
            period = response_schemas.Period(
                    id=metric.period.id,
                    start_date=metric.period.start_date.strftime("%Y-%m-%d"),
                    end_date=metric.period.end_date.strftime("%Y-%m-%d"),
                )
            periods.append(period)
            model = response_schemas.EmployeeMetrica(
                id=metric.id,
                employee_id=metric.employee_id,
                number_of_answered_emails=metric.number_of_answered_emails,
                number_of_sent_emails=metric.number_of_sent_emails,
                number_of_received_emails=metric.number_of_received_emails,
                mean_number_of_recipients_in_one_email_for_user=metric.mean_number_of_recipients_in_one_email_for_user,
                number_of_emails_read_after_x_minutes=metric.number_of_emails_read_after_x_minutes,
                mean_number_of_days_between_receiving_emails_and_read=metric.mean_number_of_days_between_receiving_emails_and_read,
                number_of_sent_emails_outside_of_working_hours=metric.number_of_sent_emails_outside_of_working_hours,
                received_and_sent_emails_proportion_for_user=metric.received_and_sent_emails_proportion_for_user,
                mean_number_of_not_answered_questions_in_email=metric.mean_number_of_not_answered_questions_in_email,
                mean_length_of_user_emails=metric.mean_length_of_user_emails,
                mean_answering_time_for_user=metric.mean_answering_time_for_user,
                number_of_passed_corporative_tests_or_courses_for_user=metric.number_of_passed_corporative_tests_or_courses_for_user,
                number_of_unique_recipients_of_emails_for_user=metric.number_of_unique_recipients_of_emails_for_user,
                number_of_unique_departments_in_emails_for_user=metric.number_of_unique_departments_in_emails_for_user,
                toxcity_in_sent_emails_for_user=metric.toxcity_in_sent_emails_for_user,
                toxcity_in_received_emails_for_user=metric.toxcity_in_received_emails_for_user,
                emotions_in_sent_emails_for_user=metric.emotions_in_sent_emails_for_user,
                emotions_in_received_emails_for_user=metric.emotions_in_received_emails_for_user,
                salary=metric.salary,
                high_priority_emails_reply_delay=metric.high_priority_emails_reply_delay,
                medium_priority_emails_reply_delay=metric.medium_priority_emails_reply_delay,
                low_priority_emails_reply_delay=metric.low_priority_emails_reply_delay,
                period=period,
            )
            metrics_list.append(model)
        df = pd.DataFrame([metric.dict() for metric in metrics_list])
        download_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../../downloads")
        # set columns to df
        df.rename(columns={
            'employee_id': 'ID Сотрудника',
            'number_of_answered_emails': 'Колличество ответов',
            'number_of_sent_emails': 'Количество отправленных писем',
            'number_of_received_emails': 'Количество полученных писем',
            'mean_number_of_recipients_in_one_email_for_user': 'Среднее количество получателей в письме',
            'number_of_emails_read_after_x_minutes': 'Количество писем, прочитанных через 60 минут после получения',
            'mean_number_of_days_between_receiving_emails_and_read': 'Среднее количество дней между получением и прочтением письма',
            'number_of_sent_emails_outside_of_working_hours': 'Количество писем, отправленных в нерабочее время',
            'received_and_sent_emails_proportion_for_user': 'Соотношение полученных и отправленных писем',
            'mean_number_of_not_answered_questions_in_email': 'Количество неотвеченных вопросов в письмах',
            'mean_length_of_user_emails': 'Средняя длина письма',
            'mean_answering_time_for_user': 'Среднее время ответа на письмо',
            'number_of_passed_corporative_tests_or_courses_for_user': 'Количество пройденных корпоративных тестов и курсов',
            'number_of_unique_recipients_of_emails_for_user': 'Количество уникальных получателей писем',
            'number_of_unique_departments_in_emails_for_user': 'Количество уникальных отделов в письмах',
            'toxcity_in_sent_emails_for_user': 'Средняя токсичность отправленных писем',
            'toxcity_in_received_emails_for_user': 'Средняя токсичность полученных писем',
            'emotions_in_sent_emails_for_user': 'Средняя эмоциональность отправленных писем',
            'emotions_in_received_emails_for_user': 'Средняя эмоциональность полученных писем',
            'salary': 'Зарплата',
            'high_priority_emails_reply_delay': 'высокая срочность',
            'medium_priority_emails_reply_delay': 'средняя срочность',
            'low_priority_emails_reply_delay': 'не срочно',
            'period': 'Период',
            }, inplace=True)
        # check if downloads folder exists
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        file_path = os.path.join(download_folder, f"employee_{id}_metrics.xlsx")
        df.to_excel(file_path, index=False)
        return file_path
    except NoResultFound:
        return None
