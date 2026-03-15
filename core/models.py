from django.db import models


class Provider(models.Model):
    """Referring provider — unique by NPI."""

    name = models.CharField(max_length=200)
    npi = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (NPI: {self.npi})"


class Patient(models.Model):
    """Patient — unique by MRN."""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    mrn = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (MRN: {self.mrn})"


class Order(models.Model):
    """One order = one patient + one medication. Links to Patient and Provider."""

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="orders")
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="orders")
    medication_name = models.CharField(max_length=200)
    primary_diagnosis = models.CharField(max_length=20)
    additional_diagnoses = models.TextField(blank=True, default="")
    medication_history = models.TextField(blank=True, default="")
    patient_records = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk}: {self.patient} — {self.medication_name}"


class CarePlan(models.Model):
    """Generated care plan — one per order."""

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="care_plan")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CarePlan for Order #{self.order_id}"
