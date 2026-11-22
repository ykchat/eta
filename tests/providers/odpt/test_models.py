from eta.models import Operator
from eta.providers.odpt.models import ODPTOperator

def test_operator_with_titles() -> None:

    operator = ODPTOperator.model_validate({
            "owl:sameAs": "odpt.Operator:Toei",
            "dc:title": "東京都交通局",
            "odpt:operatorTitle": {"ja": "東京都交通局", "en": "Bureau of Transportation, Tokyo Metropolitan Government"},
        })

    assert operator.build() == Operator(
            id = "odpt.Operator:Toei",
            name = "Toei",
            titles = {"ja": "東京都交通局", "en": "Bureau of Transportation, Tokyo Metropolitan Government"},
        )

def test_operator_without_titles() -> None:

    operator = ODPTOperator.model_validate({
            "owl:sameAs": "odpt.Operator:Rinko", 
            "dc:title": "川崎鶴見臨港バス"
        })
    operator = operator.build()

    assert operator.title("ja") == "川崎鶴見臨港バス"
    assert operator.title("en") is None

def test_operator_without_any_title() -> None:

    operator = ODPTOperator.model_validate({"owl:sameAs": "odpt.Operator:Unknown"})

    assert operator.build().titles == {}
