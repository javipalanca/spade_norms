#!/usr/bin/env python

"""Tests for `spade_norms` package."""

import pytest


from spade_norms import spade_norms

#Factory_boy
#conftest.py -> te permite definir fixtures (parametros a pasarle alos test si te hace falta) 

@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string
