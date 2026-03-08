import csv
import os
import uuid
from datetime import datetime

import anthropic
from django.http import HttpResponse
from django.shortcuts import redirect, render

# ─── In-memory storage ───────────────────────────────────────────────
# 所有数据存在这个 dict 里，重启就没了。
# 这是 MVP 故意的设计：后面会加数据库。
ORDERS = {}

# ─── LLM prompt ──────────────────────────────────────────────────────
CARE_PLAN_PROMPT = """You are a clinical pharmacist at a specialty pharmacy. \
Based on the following patient information, generate a comprehensive care plan.

Patient: {patient_first_name} {patient_last_name}
MRN: {mrn}
Primary Diagnosis (ICD-10): {primary_diagnosis}
Medication: {medication_name}
Additional Diagnoses: {additional_diagnoses}
Medication History: {medication_history}
Clinical Records/Notes: {patient_records}

Generate a care plan with EXACTLY these four sections:

1. Problem List / Drug Therapy Problems (DTPs)
2. Goals (SMART)
3. Pharmacist Interventions / Plan
4. Monitoring Plan & Lab Schedule

Be specific to this patient's diagnoses and medication. \
Include clinically appropriate recommendations."""


# ─── Views ────────────────────────────────────────────────────────────


def form_view(request):
    """GET: show empty form. POST: create order + call LLM → redirect to result."""
    if request.method == "GET":
        return render(request, "core/form.html")

    order_id = uuid.uuid4().hex[:8]
    order = {
        "id": order_id,
        "patient_first_name": request.POST["patient_first_name"],
        "patient_last_name": request.POST["patient_last_name"],
        "provider_name": request.POST["provider_name"],
        "provider_npi": request.POST["provider_npi"],
        "mrn": request.POST["mrn"],
        "primary_diagnosis": request.POST["primary_diagnosis"],
        "medication_name": request.POST["medication_name"],
        "additional_diagnoses": request.POST.get("additional_diagnoses", ""),
        "medication_history": request.POST.get("medication_history", ""),
        "patient_records": request.POST.get("patient_records", ""),
        "created_at": datetime.now().isoformat(),
    }

    # 同步调 LLM — 用户等 10-30 秒，页面一直转圈
    # 这就是后面引入消息队列要解决的痛点
    order["care_plan"] = _generate_care_plan(order)

    ORDERS[order_id] = order
    return redirect("result", order_id=order_id)


def result_view(request, order_id):
    """Display generated care plan."""
    order = ORDERS.get(order_id)
    if not order:
        return HttpResponse("Order not found", status=404)
    return render(request, "core/result.html", {"order": order})


def download_view(request, order_id):
    """Download care plan as a .txt file."""
    order = ORDERS.get(order_id)
    if not order:
        return HttpResponse("Order not found", status=404)

    content = (
        f"Care Plan\n"
        f"{'=' * 60}\n"
        f"Patient: {order['patient_first_name']} {order['patient_last_name']}\n"
        f"MRN: {order['mrn']}\n"
        f"Medication: {order['medication_name']}\n"
        f"Primary Diagnosis: {order['primary_diagnosis']}\n"
        f"Provider: {order['provider_name']} (NPI: {order['provider_npi']})\n"
        f"Generated: {order['created_at']}\n"
        f"{'=' * 60}\n\n"
        f"{order['care_plan']}\n"
    )

    resp = HttpResponse(content, content_type="text/plain; charset=utf-8")
    filename = f"care_plan_{order['mrn']}_{order['medication_name']}.txt"
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


def orders_view(request):
    """List all orders (most recent first)."""
    sorted_orders = sorted(
        ORDERS.values(), key=lambda o: o["created_at"], reverse=True
    )
    return render(request, "core/orders.html", {"orders": sorted_orders})


def export_csv(request):
    """Export all orders as CSV for pharma reporting."""
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="care_plans_export.csv"'

    writer = csv.writer(resp)
    writer.writerow([
        "Order ID", "Patient Name", "MRN", "Provider", "NPI",
        "Medication", "Primary Diagnosis", "Created At",
    ])
    for o in ORDERS.values():
        writer.writerow([
            o["id"],
            f"{o['patient_first_name']} {o['patient_last_name']}",
            o["mrn"],
            o["provider_name"],
            o["provider_npi"],
            o["medication_name"],
            o["primary_diagnosis"],
            o["created_at"],
        ])

    return resp


# ─── LLM call ─────────────────────────────────────────────────────────


def _generate_care_plan(order):
    """Call Anthropic Claude to generate a care plan. Returns the text content."""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=(
            "You are a clinical pharmacist generating care plans "
            "for a specialty pharmacy. Be professional, specific, "
            "and clinically accurate."
        ),
        messages=[
            {"role": "user", "content": CARE_PLAN_PROMPT.format(**order)},
        ],
        temperature=0.3,
    )
    return message.content[0].text
