from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

def policy_pdf_bytes(policy):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    elems = []

    title = f"Policy Document: {policy.policy_number}"
    elems.append(Paragraph(title, styles["Title"]))
    elems.append(Spacer(1, 8))

    holder_info = [
        ["Policyholder", policy.holder.full_name],
        ["National ID", policy.holder.national_id or ""],
        ["Phone", policy.holder.phone or ""],
        ["Email", policy.holder.email or ""],
        ["Address", policy.holder.address or ""],
        ["Agent", policy.agent.name if policy.agent else ""],
        ["Status", policy.status],
        ["Start Date", policy.start_date.strftime("%Y-%m-%d")],
        ["Premium", f"{policy.premium_amount:.2f}"],
        ["Benefit", f"{policy.benefit_amount:.2f} ({policy.benefit_description or ''})"],
    ]
    t = Table(holder_info, hAlign='LEFT', colWidths=[35*mm, None])
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.25,colors.grey),
                           ('BACKGROUND',(0,0),(0,-1),colors.whitesmoke),
                           ('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    elems.append(t)
    elems.append(Spacer(1, 10))

    # Members table
    member_rows = [["Full Name", "Relationship", "DOB", "National ID"]]
    for m in policy.members:
        member_rows.append([m.full_name, m.relationship or "", m.date_of_birth.strftime("%Y-%m-%d") if m.date_of_birth else "", m.national_id or ""])

    mt = Table(member_rows, hAlign='LEFT', colWidths=[60*mm, 30*mm, 30*mm, None])
    mt.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.25,colors.grey),
                            ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
                            ('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    elems.append(Paragraph("Covered Members", styles["Heading2"]))
    elems.append(mt)

    doc.build(elems)
    pdf = buf.getvalue()
    buf.close()
    return pdf
