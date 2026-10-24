import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("invoice_app", Path(__file__).parents[1] / "app.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def base():
    return {
        "invoice_number": "INV-100",
        "supplier": "Northwind",
        "amount": 250.0,
        "currency": "USD",
        "approval_status": "approved",
        "paid_status": "unpaid",
        "evidence": [{"document": "approval.pdf", "page": 1, "excerpt": "Approved", "supports": "approval"}]
    }

def test_approved_under_limit():
    assert m.decide(base())["action"] == "request_payment"

def test_missing_approval_holds():
    f = base()
    f["approval_status"] = "unknown"
    assert m.decide(f)["action"] == "hold"

def test_over_limit_holds():
    f = base()
    f["amount"] = m.MAX_APPROVED_AMOUNT + 1
    assert m.decide(f)["action"] == "hold"

def test_paid_status_blocks():
    f = base()
    f["paid_status"] = "paid"
    assert m.decide(f)["action"] == "no_action"

def test_missing_amount_holds():
    f = base()
    f["amount"] = None
    assert m.decide(f)["action"] == "hold"

def test_different_invoice_identity_differs():
    a = m.stable_key("Northwind", "INV-100")
    b = m.stable_key("Northwind", "INV-101")
    assert a != b
