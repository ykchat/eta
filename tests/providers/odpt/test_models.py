from eta.models import Operator
from eta.schemas.odpt import ODPTOperator
from eta.providers.odpt.provider import ODPTJSONProvider

def test_operator_with_titles() -> None:

    odpt = ODPTOperator.model_validate({
            "owl:sameAs": "odpt.Operator:Toei",
            "dc:title": "東京都交通局",
            "odpt:operatorTitle": {"ja": "東京都交通局", "en": "Bureau of Transportation, Tokyo Metropolitan Government"},
        })

    assert ODPTJSONProvider.build_operator(odpt) == Operator(
            id = "odpt.Operator:Toei",
            name = "Toei",
            titles = {"ja": "東京都交通局", "en": "Bureau of Transportation, Tokyo Metropolitan Government"},
        )

def test_operator_without_titles() -> None:

    odpt = ODPTOperator.model_validate({
            "owl:sameAs": "odpt.Operator:Rinko", 
            "dc:title": "川崎鶴見臨港バス"
        })

    operator = ODPTJSONProvider.build_operator(odpt) 

    assert operator.title("ja") == "川崎鶴見臨港バス"
    assert operator.title("en") is None

def test_operator_without_any_title() -> None:

    odpt = ODPTOperator.model_validate({"owl:sameAs": "odpt.Operator:Unknown"})

    assert ODPTJSONProvider.build_operator(odpt).titles == {}
