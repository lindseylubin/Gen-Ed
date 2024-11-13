# SPDX-FileCopyrightText: 2023 Mark Liffiton <liffiton@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-only

import datetime as dt
from sqlite3 import Row

from flask import (
    Blueprint,
    abort,
    flash,
    render_template,
    request,
)
from werkzeug.wrappers.response import Response

from .auth import get_auth, instructor_required
from .csv import csv_response
from .db import get_db
from .redir import safe_redirect

bp = Blueprint('instructor', __name__, url_prefix="/instructor", template_folder='templates')

@bp.before_request
@instructor_required
def before_request() -> None:
    """ Apply decorator to protect all instructor blueprint endpoints. """


def get_queries(class_id: int, user: int | None = None) -> list[Row]:
    db = get_db()

    where_clause = "WHERE UNLIKELY(roles.class_id=?)"  # UNLIKELY() to help query planner in older sqlite versions
    params = [class_id]

    if user is not None:
        where_clause += " AND users.id=?"
        params += [user]

    queries = db.execute(f"""
        SELECT
            queries.id,
            users.display_name,
            users.email,
            queries.*
        FROM queries
        JOIN users
            ON queries.user_id=users.id
        JOIN roles
            ON queries.role_id=roles.id
        {where_clause}
        ORDER BY queries.id DESC
    """, params).fetchall()

    return queries

def get_summary(class_id: int, user: int, context: int | None = None) -> list[Row]:
    db = get_db()
    where_clause = "WHERE UNLIKELY(roles.class_id=?)"  # UNLIKELY() to help query planner in older sqlite versions
    params = [class_id]

    if user is not None:
        where_clause += " AND users.id=?"
        params += [user]
    if context is not None:
        where_clause += " AND contexts.id=?"
        params += [context]


    # Query to retrieve all table names
    summary = db.execute(f"""
            SELECT 
                queries.id,
                context_string_id,
                context_name,
                users.display_name,
                strftime('%Y-%m-%d', query_time) AS query_date,  -- Extract date
                strftime('%H:%M:%S', query_time) AS query_time  -- Extract time
            FROM queries
            JOIN contexts
                ON queries.context_name=contexts.name
            JOIN users
                ON queries.user_id=users.id
            JOIN roles
                ON queries.role_id=roles.id
            {where_clause}
            ORDER BY queries.id DESC
        """, params).fetchall()
    return summary

def get_contexts(class_id: int, for_export: bool = False) -> list[Row]:
    db = get_db()

    contexts = db.execute(f"""
        SELECT
            contexts.id,
            contexts.name,
            contexts.class_id,
            contexts.available
        FROM contexts         
        WHERE contexts.class_id=?
        GROUP BY contexts.id
        ORDER BY name
    """, [class_id]).fetchall()

    return contexts

def get_users(class_id: int, for_export: bool = False) -> list[Row]:
    db = get_db()

    users = db.execute(f"""
        SELECT
            {'roles.id AS role_id,' if not for_export else ''}
            users.id,
            users.display_name,
            users.email,
            auth_providers.name AS auth_provider,
            users.auth_name,
            COUNT(queries.id) AS num_queries,
            SUM(CASE WHEN queries.query_time > date('now', '-7 days') THEN 1 ELSE 0 END) AS num_recent_queries,
            roles.active,
            roles.role = "instructor" AS instructor_role
        FROM users
        LEFT JOIN auth_providers ON users.auth_provider=auth_providers.id
        JOIN roles ON roles.user_id=users.id
        LEFT JOIN queries ON queries.role_id=roles.id
        WHERE roles.class_id=?
        GROUP BY users.id
        ORDER BY display_name
    """, [class_id]).fetchall()

    return users


def get_tables():
    db = get_db()
    cursor = db.cursor()
     # Query to retrieve all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("Table Names:")
    for table in tables:
        print(table["name"])  # Accessing the name directly if using sqlite3.Row

    queries = cursor.execute(f"""
        PRAGMA table_info(context_strings);
    """).fetchall()

    # Print the column names
    print("Column Names:")
    for column in queries:
        print(column["name"])  # The column name is in the second element

@bp.route('/api/data', methods=['GET'])
def get_data():
    data = get_db()
    # Convert data to JSON-friendly format, e.g., list of dictionaries
    json_data = [{"column1": row[0], "column2": row[1]} for row in data]
    #return jsonify(json_data)

@bp.route("/")
def main() -> str | Response:
    auth = get_auth()
    class_id = auth['class_id']
    assert class_id is not None

    users = get_users(class_id)
    contexts = get_contexts(class_id)
    

    sel_user_name = None
    sel_user_id = request.args.get('user', type=int)
    if sel_user_id is not None:
        sel_user_row = next(filter(lambda row: row['id'] == int(sel_user_id), users), None)
        if sel_user_row:
            sel_user_name = sel_user_row['display_name']

    sel_context_name = None
    sel_context_id = request.args.get('context', type=int)
    if sel_context_id is not None:
        sel_context_row = next(filter(lambda row: row['id'] == int(sel_context_id), contexts), None)
        if sel_context_row:
            sel_context_name = sel_context_row['name']

    summary = get_summary(class_id, sel_user_id, sel_context_id)
    queries = get_queries(class_id, sel_user_id)
    get_tables()


    return render_template("instructor.html",contexts=contexts, users=users, summary=summary, queries=queries, user=sel_user_name, context=sel_context_name)


@bp.route("/csv/<string:kind>")
def get_csv(kind: str) -> str | Response:
    if kind not in ('queries', 'users'):
        return abort(404)

    auth = get_auth()
    class_id = auth['class_id']
    class_name = auth['class_name']
    assert class_id is not None
    assert class_name is not None

    if kind == "queries":
        table = get_queries(class_id)
    elif kind == "users":
        table = get_users(class_id, for_export=True)

    return csv_response(class_name, kind, table)


@bp.route("/user_class/set", methods=["POST"])
def set_user_class_setting() -> Response:
    db = get_db()
    auth = get_auth()

    # only trust class_id from auth, not from user
    class_id = auth['class_id']

    if 'clear_openai_key' in request.form:
        db.execute("UPDATE classes_user SET openai_key='' WHERE class_id=?", [class_id])
        db.commit()
        flash("Class API key cleared.", "success")

    elif 'save_access_form' in request.form:
        if 'link_reg_active_present' in request.form:
            # only present for user classes, not LTI
            link_reg_active = request.form['link_reg_active']
            if link_reg_active == "disabled":
                new_date = str(dt.date.min)
            elif link_reg_active == "enabled":
                new_date = str(dt.date.max)
            else:
                new_date = request.form['link_reg_expires']
            db.execute("UPDATE classes_user SET link_reg_expires=? WHERE class_id=?", [new_date, class_id])
        class_enabled = 1 if 'class_enabled' in request.form else 0
        db.execute("UPDATE classes SET enabled=? WHERE id=?", [class_enabled, class_id])
        db.commit()
        flash("Class access configuration updated.", "success")

    elif 'save_llm_form' in request.form:
        if 'openai_key' in request.form:
            db.execute("UPDATE classes_user SET openai_key=? WHERE class_id=?", [request.form['openai_key'], class_id])
        db.execute("UPDATE classes_user SET model_id=? WHERE class_id=?", [request.form['model_id'], class_id])
        db.commit()
        flash("Class language model configuration updated.", "success")

    return safe_redirect(request.referrer, default_endpoint="profile.main")


@bp.route("/role/set_active", methods=["POST"])  # just for url_for in the Javascript code
@bp.route("/role/set_active/<int:role_id>/<int(min=0, max=1):bool_active>", methods=["POST"])
def set_role_active(role_id: int, bool_active: int) -> str:
    db = get_db()
    auth = get_auth()

    # prevent instructors from mistakenly making themselves not active and locking themselves out
    if role_id == auth['role_id']:
        return "You cannot make yourself inactive."

    # class_id should be redundant w/ role_id, but without it, an instructor
    # could potentially deactivate a role in someone else's class.
    # only trust class_id from auth, not from user
    class_id = auth['class_id']

    db.execute("UPDATE roles SET active=? WHERE id=? AND class_id=?", [bool_active, role_id, class_id])
    db.commit()

    return "okay"


@bp.route("/role/set_instructor", methods=["POST"])  # just for url_for in the Javascript code
@bp.route("/role/set_instructor/<int:role_id>/<int(min=0, max=1):bool_instructor>", methods=["POST"])
def set_role_instructor(role_id: int, bool_instructor: int) -> str:
    db = get_db()
    auth = get_auth()

    # prevent instructors from mistakenly making themselves not instructors and locking themselves out
    if role_id == auth['role_id']:
        return "You cannot change your own role."

    # class_id should be redundant w/ role_id, but without it, an instructor
    # could potentially deactivate a role in someone else's class.
    # only trust class_id from auth, not from user
    class_id = auth['class_id']

    new_role = 'instructor' if bool_instructor else 'student'

    db.execute("UPDATE roles SET role=? WHERE id=? AND class_id=?", [new_role, role_id, class_id])
    db.commit()

    return "okay"
