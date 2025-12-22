import pytest
from tests.api_tests import Aux_Library as aux

pytestmark = pytest.mark.order(5)

@pytest.fixture(scope="module")
def test_user():
    """
    Define a test user and ensure a clean state.
    """
    username = "john_doe"
    # Ensure clean slate
    aux.remove_domains(["pytest-example.com", "bulk0.example.com", "bulk1.example.com", "bulk2.example.com"], username)
    return username

def test_1_add_and_remove_domain(test_user):
    """
    Full add/remove domain test with Normalization Check.
    """
    input_domain = "pytest-example.com"
    username = test_user

    # 1. Add domain
    add_resp = aux.add_domain(input_domain, username)
    assert add_resp.status_code in (201, 409)
    assert "ok" in add_resp.json()
    
    saved_domain_name = add_resp.json().get("domain") or input_domain
    print(f"[INFO] Server saved domain as: '{saved_domain_name}'")

    # 2. Verify domain list
    list_resp = aux.list_domains(username)
    assert list_resp.status_code == 200
    
    # Raw list of dictionaries: [{'domain': '...', 'status': '...'}, ...]
    domains_data = list_resp.json().get("domains", [])
    
    # FIX: Extract just the domain strings for comparison
    domain_names = [d.get("domain") for d in domains_data]
    print(f"[INFO] Current domain names in DB: {domain_names}")

    assert saved_domain_name in domain_names, \
        f"Domain '{saved_domain_name}' not found in list: {domain_names}"

    # 3. Remove domain
    remove_resp = aux.remove_domains([saved_domain_name], username)
    assert remove_resp.status_code == 200
    assert remove_resp.json().get("ok") is True

    # 4. Confirm removal
    verify_resp = aux.list_domains(username)
    domains_after_data = verify_resp.json().get("domains", [])
    domain_names_after = [d.get("domain") for d in domains_after_data]
    
    assert saved_domain_name not in domain_names_after, "Domain still present after removal"


def test_2_remove_domain_without_auth():
    """Removing a domain without X-Username header should fail."""
    resp = aux.remove_domains(["unauth.com"], username="")
    # Expecting 401 Unauthorized
    assert resp.status_code == 401, f"Should be 401, got {resp.status_code}"


def test_3_remove_nonexistent_domain(test_user):
    """Removing a non-existent domain."""
    domain = "this-domain-does-not-exist.com"
    username = test_user

    resp = aux.remove_domains([domain], username)
    
    # 200 OK is acceptable (idempotent)
    assert resp.status_code == 200
    assert "ok" in resp.json()


def test_4_remove_domains_bulk(test_user):
    """Add several domains and remove them all in one API call."""
    username = test_user
    domains = [f"bulk{i}.example.com" for i in range(3)]

    # Add all and capture saved names
    saved_names = []
    for d in domains:
        resp = aux.add_domain(d, username)
        saved_names.append(resp.json().get("domain"))

    # Remove all at once
    rem_resp = aux.remove_domains(saved_names, username)
    assert rem_resp.status_code == 200
    assert rem_resp.json().get("ok") is True

    # Verify none remain
    list_resp = aux.list_domains(username)
    current_data = list_resp.json().get("domains", [])
    current_names = [d.get("domain") for d in current_data]
    
    for d in saved_names:
        assert d not in current_names, f"{d} still present after bulk removal"


def test_5_remove_domains_empty_payload(test_user):
    """Removing domains with empty list should return 400."""
    username = test_user
    resp = aux.remove_domains([], username)
    
    assert resp.status_code == 400
    assert "error" in resp.json()