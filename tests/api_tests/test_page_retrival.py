from .Aux_Library import check_get_webpage
import pytest

pytestmark = pytest.mark.order(1)

@pytest.mark.parametrize("PATH", [
    "/",
    "/login",
    "/register",
    "/dashboard"
])
def test_1_page_retrival(PATH):
    response = check_get_webpage(PATH)
    assert response.status_code == 200