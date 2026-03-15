import csv
import os

import anthropic
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .models import CarePlan, Order, Patient, Provider

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

    # Get or create provider (keyed by NPI)
    provider, _ = Provider.objects.get_or_create(
        npi=request.POST["provider_npi"],
        defaults={"name": request.POST["provider_name"]},
    )

    # Get or create patient (keyed by MRN)
    patient, _ = Patient.objects.get_or_create(
        mrn=request.POST["mrn"],
        defaults={
            "first_name": request.POST["patient_first_name"],
            "last_name": request.POST["patient_last_name"],
        },
    )

    # Create order
    order = Order.objects.create(
        patient=patient,
        provider=provider,
        medication_name=request.POST["medication_name"],
        primary_diagnosis=request.POST["primary_diagnosis"],
        additional_diagnoses=request.POST.get("additional_diagnoses", ""),
        medication_history=request.POST.get("medication_history", ""),
        patient_records=request.POST.get("patient_records", ""),
    )

    # 同步调 LLM — 用户等 10-30 秒
    content = _generate_care_plan(order)
    CarePlan.objects.create(order=order, content=content)

    return redirect("result", order_id=order.pk)


def result_view(request, order_id):
    """Display generated care plan."""
    try:
        order = Order.objects.select_related(
            "patient", "provider", "care_plan"
        ).get(pk=order_id)
    except Order.DoesNotExist:
        return HttpResponse("Order not found", status=404)
    return render(request, "core/result.html", {"order": order})


def download_view(request, order_id):
    """Download care plan as a .txt file."""
    try:
        order = Order.objects.select_related(
            "patient", "provider", "care_plan"
        ).get(pk=order_id)
    except Order.DoesNotExist:
        return HttpResponse("Order not found", status=404)

    text = (
        f"Care Plan\n"
        f"{'=' * 60}\n"
        f"Patient: {order.patient.first_name} {order.patient.last_name}\n"
        f"MRN: {order.patient.mrn}\n"
        f"Medication: {order.medication_name}\n"
        f"Primary Diagnosis: {order.primary_diagnosis}\n"
        f"Provider: {order.provider.name} (NPI: {order.provider.npi})\n"
        f"Generated: {order.created_at}\n"
        f"{'=' * 60}\n\n"
        f"{order.care_plan.content}\n"
    )

    resp = HttpResponse(text, content_type="text/plain; charset=utf-8")
    filename = f"care_plan_{order.patient.mrn}_{order.medication_name}.txt"
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


def orders_view(request):
    """List all orders (most recent first)."""
    orders = Order.objects.select_related("patient", "provider").order_by("-created_at")
    return render(request, "core/orders.html", {"orders": orders})


def export_csv(request):
    """Export all orders as CSV for pharma reporting."""
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="care_plans_export.csv"'

    writer = csv.writer(resp)
    writer.writerow([
        "Order ID", "Patient Name", "MRN", "Provider", "NPI",
        "Medication", "Primary Diagnosis", "Created At",
    ])
    for o in Order.objects.select_related("patient", "provider").all():
        writer.writerow([
            o.pk,
            f"{o.patient.first_name} {o.patient.last_name}",
            o.patient.mrn,
            o.provider.name,
            o.provider.npi,
            o.medication_name,
            o.primary_diagnosis,
            o.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return resp


# ─── LLM call ─────────────────────────────────────────────────────────


def _generate_care_plan(order):
    """Call Anthropic Claude to generate a care plan. Returns the text content."""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    context = {
        "patient_first_name": order.patient.first_name,
        "patient_last_name": order.patient.last_name,
        "mrn": order.patient.mrn,
        "primary_diagnosis": order.primary_diagnosis,
        "medication_name": order.medication_name,
        "additional_diagnoses": order.additional_diagnoses,
        "medication_history": order.medication_history,
        "patient_records": order.patient_records,
    }

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=(
            "You are a clinical pharmacist generating care plans "
            "for a specialty pharmacy. Be professional, specific, "
            "and clinically accurate."
        ),
        messages=[
            {"role": "user", "content": CARE_PLAN_PROMPT.format(**context)},
        ],
        temperature=0.3,
    )
    return message.content[0].text
