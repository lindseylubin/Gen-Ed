# SPDX-FileCopyrightText: 2023 Mark Liffiton <liffiton@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    session,
    url_for,
)
from pylti.flask import lti
from werkzeug.wrappers.response import Response

from .auth import (
    ext_login_update_or_create,
    set_session_auth_role,
    set_session_auth_user,
)
from .classes import get_or_create_lti_class
from .db import get_db

bp = Blueprint('lti', __name__, url_prefix="/lti", template_folder='templates')


# An LTI-specific error handler
def lti_error(exception: dict[str, Any]) -> tuple[str, int]:
    """Log the error and render a simple error page."""
    current_app.logger.error(f"LTI exception: {exception['exception']=} {exception['kwargs']=} {exception['args']=}")
    return "There was an LTI communication error", 500


# Handles LTI 1.0/1.1 initial request / login
# https://github.com/mitodl/pylti/blob/master/pylti/flask.py
# https://github.com/mitodl/mit_lti_flask_sample
@bp.route("/", methods=['GET', 'POST'])
@lti(request='initial', error=lti_error)
def lti_login(lti=lti) -> Response | tuple[str, int]:
    authenticated = session.get("lti_authenticated", False)
    role = session.get("roles", "").lower()
    full_name = session.get("lis_person_name_full", None)
    email = session.get("lis_person_contact_email_primary", None)
    lti_user_id = session.get("user_id", "")
    lti_consumer = session.get("oauth_consumer_key", "")
    lti_context_id = session.get("context_id", "")
    class_name = session.get("context_label", "")

    current_app.logger.debug(f"LTI login: {lti_consumer=} {full_name=} {email=} {role=} {class_name=}")

    # sanity checks
    if not authenticated:
        current_app.logger.warning("LTI login not authenticated.")
        session.clear()
        return abort(403)

    if not lti_user_id or not lti_consumer or not lti_context_id or not class_name:
        current_app.logger.warning(f"LTI login missing one of: {lti_user_id=} {lti_consumer=} {lti_context_id=} {class_name=}")
        session.clear()
        return abort(400)

    if not full_name and (not email or '@' not in email):
        current_app.logger.warning(f"LTI login missing name or email: {lti_consumer=} {full_name=} {email=}")
        session.clear()
        flash("LTI login missing name and email (at least one required).", "danger")
        return render_template("error.html"), 400

    # check for instructors
    instructor_role_substrs = ["instructor", "teachingassistant"]
    if any(substr in role.lower() for substr in instructor_role_substrs):
        role = "instructor"
    else:
        # anything else becomes "student"
        role = "student"

    db = get_db()

    # grab consumer ID (must exist, since the LTI processing must have used it to get here with success)
    consumer_row = db.execute("SELECT id FROM consumers WHERE lti_consumer=?", [lti_consumer]).fetchone()
    lti_consumer_id = consumer_row['id']

    # check for and create class if needed
    class_id = get_or_create_lti_class(lti_consumer_id, lti_context_id, class_name)

    # check for and create user account if needed
    lti_id = f"{lti_consumer}_{lti_user_id}_{email}"
    user_normed = {
        'email': email,
        'full_name': full_name,
        'auth_name': None,
        'ext_id': lti_id,
    }
    # LTI users given 0 tokens by default -- should only ever use API registered w/ LTI consumer
    user_row = ext_login_update_or_create('lti', user_normed, query_tokens=10)
    user_id = user_row['id']

    # check for and create role if needed
    role_row = db.execute(
        "SELECT * FROM roles WHERE user_id=? AND class_id=?", [user_id, class_id]
    ).fetchone()

    if not role_row:
        # Register this user
        cur = db.execute("INSERT INTO roles(user_id, class_id, role) VALUES(?, ?, ?)", [user_id, class_id, role])
        db.commit()
        role_id = cur.lastrowid
    else:
        role_id = role_row['id']

        if not role_row['active']:
            session.clear()
            return abort(403)

    # Record them as logged in in the session
    set_session_auth_user(user_id)
    set_session_auth_role(role_id)

    # Redirect to the app
    return redirect(url_for("helper.help_form"))


@bp.route("/config.xml")
def lti_config() -> tuple[str, int, dict[str, str]]:
    return render_template("lti_config.xml"), 200, {'Content-Type': 'text/xml'}


#@bp.route("debug", methods=['GET'])
#@lti(request='session')
#def lti_debug(lti=lti):
#    return {var: session[var] for var in session}
