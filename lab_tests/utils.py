
from lab_tests.models import LabTestResultOrder

def check_and_create_result_order(request_order):
    if request_order.all_samples_collected():
        LabTestResultOrder.objects.get_or_create(
            lab_test_request=request_order,
            medical_record=request_order.medical_record,
            patient_type=request_order.patient_type,
            defaults={
                "status": "Pending"
            }
        )
