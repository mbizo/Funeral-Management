import os
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
from . import db
from .models import Agent, Policy, PolicyHolder, Member, Payment, Commission
from .utils import generate_policy_number, env_admin_password
from .pdf import policy_pdf_bytes
from io import BytesIO

bp = Blueprint("core", __name__)

# -------- Simple auth (single admin) --------
@bp.before_app_request
def require_login():
    public_paths = {"core.login", "static"}
    if request.endpoint is None:
        return
    if request.endpoint.split(".")[0] == "static":
        return
    if request.endpoint in public_paths:
        return
    if not session.get("user"):
        return redirect(url_for("core.login"))

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        if username == "admin" and password == env_admin_password():
            session["user"] = "admin"
            return redirect(url_for("core.dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("core.login"))

# -------- Dashboard --------
@bp.route("/")
def dashboard():
    total_agents = Agent.query.count()
    total_policies = Policy.query.count()
    active_policies = Policy.query.filter_by(status="Active").count()
    lapsed_policies = Policy.query.filter_by(status="Lapsed").count()
    new_today = Policy.query.filter(Policy.created_at >= datetime.utcnow().date()).count()
    return render_template("dashboard.html",
                           total_agents=total_agents,
                           total_policies=total_policies,
                           active_policies=active_policies,
                           lapsed_policies=lapsed_policies,
                           new_today=new_today)

# -------- Agents --------
@bp.route("/agents", methods=["GET","POST"])
def agents():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form.get("email")
        phone = request.form.get("phone")
        rate = float(request.form.get("commission_rate", "0.10"))
        a = Agent(name=name, email=email, phone=phone, commission_rate=rate)
        db.session.add(a)
        db.session.commit()
        flash("Agent created", "success")
        return redirect(url_for("core.agents"))
    agents = Agent.query.order_by(Agent.created_at.desc()).all()
    return render_template("agents.html", agents=agents)

@bp.route("/agents/<int:agent_id>")
def agent_detail(agent_id):
    agent = Agent.query.get_or_404(agent_id)
    # commissions summary
    from sqlalchemy import func
    total_comm = db.session.query(func.sum(Commission.amount)).filter_by(agent_id=agent.id).scalar() or 0.0
    return render_template("agent_detail.html", agent=agent, total_comm=total_comm)

# -------- Policies --------
@bp.route("/policies")
def policies():
    status = request.args.get("status")
    q = Policy.query
    if status:
        q = q.filter_by(status=status)
    policies = q.order_by(Policy.created_at.desc()).all()
    return render_template("policies.html", policies=policies, status=status)

@bp.route("/policies/new", methods=["GET","POST"])
def policy_new():
    if request.method == "POST":
        holder_name = request.form["holder_name"].strip()
        holder_id = request.form.get("holder_national_id")
        holder_phone = request.form.get("holder_phone")
        holder_email = request.form.get("holder_email")
        holder_address = request.form.get("holder_address")

        agent_id = request.form.get("agent_id") or None
        premium = float(request.form.get("premium_amount","0") or 0)
        benefit_amount = float(request.form.get("benefit_amount","0") or 0)
        benefit_description = request.form.get("benefit_description")
        grace_days = int(request.form.get("grace_days","30"))

        holder = PolicyHolder(full_name=holder_name, national_id=holder_id, phone=holder_phone,
                              email=holder_email, address=holder_address)
        db.session.add(holder)
        db.session.flush()  # get holder.id

        policy_number = generate_policy_number()
        policy = Policy(policy_number=policy_number, holder_id=holder.id, agent_id=agent_id if agent_id else None,
                        premium_amount=premium, benefit_amount=benefit_amount, benefit_description=benefit_description,
                        start_date=date.today(), grace_days=grace_days, status="Active")
        db.session.add(policy)
        db.session.commit()
        flash(f"Policy {policy.policy_number} created", "success")
        return redirect(url_for("core.policy_detail", policy_id=policy.id))

    agents = Agent.query.all()
    return render_template("policy_form.html", agents=agents, policy=None)

@bp.route("/policies/<int:policy_id>", methods=["GET","POST"])
def policy_detail(policy_id):
    policy = Policy.query.get_or_404(policy_id)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_member":
            full_name = request.form["full_name"].strip()
            rel = request.form.get("relationship")
            dob = request.form.get("date_of_birth") or None
            from datetime import datetime as dt
            dob_parsed = dt.strptime(dob, "%Y-%m-%d").date() if dob else None
            nid = request.form.get("national_id")
            m = Member(policy_id=policy.id, full_name=full_name, relationship=rel,
                       date_of_birth=dob_parsed, national_id=nid)
            db.session.add(m)
            db.session.commit()
            flash("Member added", "success")
        elif action == "record_payment":
            amount = float(request.form.get("amount","0"))
            p = Payment(policy_id=policy.id, amount=amount)
            db.session.add(p)
            db.session.flush()
            # commission if agent exists
            if policy.agent:
                rate = policy.agent.commission_rate or 0.0
                c = Commission(agent_id=policy.agent.id, payment_id=p.id, amount=amount*rate)
                db.session.add(c)
            # refresh status
            policy.refresh_status()
            db.session.commit()
            flash("Payment recorded & status updated", "success")
        elif action == "update_policy":
            policy.premium_amount = float(request.form.get("premium_amount", policy.premium_amount))
            policy.benefit_amount = float(request.form.get("benefit_amount", policy.benefit_amount))
            policy.benefit_description = request.form.get("benefit_description")
            policy.status = request.form.get("status", policy.status)
            policy.grace_days = int(request.form.get("grace_days", policy.grace_days))
            db.session.commit()
            flash("Policy updated", "success")

        return redirect(url_for("core.policy_detail", policy_id=policy.id))

    policy.refresh_status()
    db.session.commit()
    agents = Agent.query.all()
    return render_template("policy_detail.html", policy=policy, agents=agents)

@bp.route("/policies/<int:policy_id>/document.pdf")
def policy_document(policy_id):
    policy = Policy.query.get_or_404(policy_id)
    pdf = policy_pdf_bytes(policy)
    return send_file(BytesIO(pdf), mimetype="application/pdf", as_attachment=True,
                     download_name=f"{policy.policy_number}.pdf")

# -------- Payments overview --------
@bp.route("/payments")
def payments():
    pays = Payment.query.order_by(Payment.paid_at.desc()).limit(200).all()
    return render_template("payments.html", payments=pays)

# -------- Reports --------
@bp.route("/reports", methods=["GET","POST"])
def reports():
    ctx = {}
    if request.method == "POST":
        report_type = request.form.get("report_type")
        start = request.form.get("start_date")
        end = request.form.get("end_date")

        start_dt = datetime.strptime(start, "%Y-%m-%d") if start else datetime.min
        end_dt = datetime.strptime(end, "%Y-%m-%d") if end else datetime.max

        if report_type == "new_policies":
            q = Policy.query.filter(Policy.created_at >= start_dt, Policy.created_at <= end_dt).order_by(Policy.created_at.desc())
            ctx["new_policies"] = q.all()
        elif report_type == "active_policies":
            ctx["active_policies"] = Policy.query.filter_by(status="Active").all()
        elif report_type == "lapsed_policies":
            ctx["lapsed_policies"] = Policy.query.filter_by(status="Lapsed").all()
        elif report_type == "agent_commissions":
            # Filter commissions by payment date through join
            from sqlalchemy.orm import joinedload
            from sqlalchemy import and_
            q = db.session.query(Commission).join(Payment).options(joinedload(Commission.agent)).filter(
                and_(Payment.paid_at >= start_dt, Payment.paid_at <= end_dt)
            ).order_by(Payment.paid_at.desc())
            ctx["commissions"] = q.all()
        else:
            pass
        ctx["report_type"] = report_type
        ctx["start_date"] = start
        ctx["end_date"] = end

    return render_template("reports.html", **ctx)
