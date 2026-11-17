"""Filo: sunucu ve runbook otomasyonu adminlik işlerini yapay zekâ ajanına yaptıran, modelden bağımsız harness.

Dili anlamak, plan kurmak, hatayı yorumlamak modelin işidir; hedef çözümleme, yürütme, şema, yetki, onay ve denetim
kodun işidir.
"""
import pathlib

__version__ = "0.1.0"

ROOT = pathlib.Path(__file__).resolve().parent.parent
SONUC = ROOT / "results"
AYARLAR = ROOT / "ayarlar"
