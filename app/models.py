from datetime import datetime, timedelta
from . import db

class Sequence(db.Model):
    __tablename__ = "sequences"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Integer, default=0, nullable=False)

    @staticmethod
    def next_val(name: str) -> int:
        seq = Sequence.query.filter_by(name=name).first()
        if not seq:
            seq = Sequence(name=name, value=1)
            db.session.add(seq)
        else:
            seq.value += 1
        db.session.commit()
        return seq.value

class Agent(db.Model):
    __tablename__ = "agents"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    commission_rate = db.Column(db.Float, default=0.10)  # 10% default
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    policies = db.relationship("Policy", backref="agent", lazy=True)
    commissions = db.relationship("Commission", backref="agent", lazy=True)

class PolicyHolder(db.Model):
    __tablename__ = "policy_holders"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    national_id = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    policies = db.relationship("Policy", backref="holder", lazy=True)

class Policy(db.Model):
    __tablename__ = "policies"
    id = db.Column(db.Integer, primary_key=True)
    policy_number = db.Column(db.String(50), unique=True, nullable=False)
    holder_id = db.Column(db.Integer, db.ForeignKey("policy_holders.id"), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey("agents.id"), nullable=True)

    premium_amount = db.Column(db.Float, nullable=False, default=0.0)
    benefit_amount = db.Column(db.Float, nullable=False, default=0.0)
    benefit_description = db.Column(db.String(255), nullable=True)

    start_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Active")  # Active / Lapsed / Cancelled
    grace_days = db.Column(db.Integer, default=30)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship("Member", backref="policy", lazy=True, cascade="all, delete-orphan")
    payments = db.relationship("Payment", backref="policy", lazy=True, cascade="all, delete-orphan")

    def refresh_status(self):
        # Active if last payment within grace_days; else Lapsed
        if not self.payments:
            self.status = "Lapsed"
            return
        last_pay = max(p.paid_at for p in self.payments)
        if (datetime.utcnow().date() - last_pay.date()).days <= self.grace_days:
            self.status = "Active"
        else:
            self.status = "Lapsed"

class Member(db.Model):
    __tablename__ = "members"
    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey("policies.id"), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    relationship = db.Column(db.String(50), nullable=True)  # e.g., Spouse, Child
    date_of_birth = db.Column(db.Date, nullable=True)
    national_id = db.Column(db.String(50), nullable=True)

class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey("policies.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)

    commission = db.relationship("Commission", backref="payment", uselist=False, cascade="all, delete-orphan")

class Commission(db.Model):
    __tablename__ = "commissions"
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey("agents.id"), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey("payments.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
