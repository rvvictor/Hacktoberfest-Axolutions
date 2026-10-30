"""HACK-073: research keeps a competitor's own business site, not PDFs, directory profiles or map listings.

The rejected URLs are the real ones returned by the HACK-071 run (PR #79).
"""
import pytest

from app.schemas import ResearchItem
from app.services.research import is_competitor_page

REJECTED = [
    ("Bombas de Agua Catálogo", "https://www.aiguapres.es/catalago-bombas-agua.pdf"),
    (
        "CATALOGO BOMBA DE AGUA 2018 V2.indd",
        (
            "https://www.drivparts.com/content/dam/marketing/mexico/catalogs/light-vehicle/"
            "SealedPower-Bomba-De-Agua-Refrigerante-2018.pdf"
        ),
    ),
    (
        "Proveedora de Bombas, Motores y Compresores, S.A. de C.V. Information",
        "https://rocketreach.co/proveedora-de-bombas-motores-y-compresores-sa-de-cv-profile_b42794f9ff19a1a6",
    ),
    (
        "Servicios Miva, Coronado, Vía Interamericana, Coronado, PA - MapQuest",
        "https://www.mapquest.com/pa/servicios-miva-coronado-431263679",
    ),
    (
        "Bombas y Control de Fluidos S.A. de C.V. Information",
        "https://rocketreach.co/bombas-y-control-de-fluidos-sa-de-cv-profile_b54af977f6646a3c",
    ),
]

ACCEPTED = [
    ("Payhawk", "https://payhawk.com/product-expense-management"),
    ("Bombas y Equipos", "https://www.bombasyequipos.example/productos"),
]


@pytest.mark.parametrize(("title", "url"), REJECTED)
def test_pdfs_directories_and_maps_are_not_competitors(title, url):
    assert not is_competitor_page(ResearchItem(competitor=title, url=url))


@pytest.mark.parametrize(("title", "url"), ACCEPTED)
def test_business_sites_stay(title, url):
    assert is_competitor_page(ResearchItem(competitor=title, url=url))


def test_pdf_is_dropped_on_any_host_and_case():
    assert not is_competitor_page(ResearchItem(competitor="Catalog", url="https://acme.test/files/Catalog.PDF"))
