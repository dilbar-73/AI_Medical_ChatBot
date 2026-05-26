
from django.contrib import admin
from .models import Consultation, Patient, PatientInfo, UserProfile


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name", "question", "diagnosis")
    readonly_fields = ("created_at",)


@admin.register(PatientInfo)
class PatientInfoAdmin(admin.ModelAdmin):
    list_display = ("id", "referral_number", "name", "phone", "specialization", "created_at")
    list_filter = ("specialization", "gender", "created_at")
    search_fields = ("referral_number", "name", "phone", "email")
    readonly_fields = ("created_at",)


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_name", "short_diagnosis", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("patient__name", "patient__referral_number", "diagnosis", "symptoms")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Patient")
    def patient_name(self, obj):
        return obj.patient.name if obj.patient else "-"

    @admin.display(description="Diagnosis")
    def short_diagnosis(self, obj):
        if not obj.diagnosis:
            return "-"
        return obj.diagnosis[:80] + ("..." if len(obj.diagnosis) > 80 else "")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "email", "phone", "specialization")
    search_fields = ("user__username", "email", "phone")
    list_filter = ("specialization", "gender")
