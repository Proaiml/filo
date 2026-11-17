# Bölüm B - Mevcut bench taraması (filo düzeyinde sunucu adminliği)

Hedef ölçüt (karşılaştırma için): çok sunucuda çalıştır-topla-raporla, kısmi başarısızlık ve yeniden deneme, kurulum + doğrulama, runbook uygulaması, sonuçların e-posta/dosyaya dönüştürülmesi.

Not: Sayılar arama özetlerinden alındı; birincil makale ya da resmi sayfa her satır için tek tek açılmadı. Belirsiz değerler "(doğrulanmadı)" ile işaretli.

## Tablo

| Ad | Ne ölçüyor | Görev sayısı | Ortam | Hedefimizle örtüşme | Not |
|---|---|---|---|---|---|
| ITBench (IBM, ICML 2025) | SRE, CISO, FinOps olay/uyum senaryoları; ajan kök neden bulur | ~102 senaryo (başlangıç); bir özet 94 diyor | Simüle BT ortamları; kod: github.com/ibm/itbench | Düşük-orta: olay teşhisi var, çok sunuculu komut dağıtımı, kurulum ve raporlama yok | ITBench-AA (Mayıs 2026): 59 SRE görevi, en iyi %47 (doğrulanmadı) |
| AIOpsLab (Microsoft, SoCC'24 / MLSys'25) | Bulut mikroservisinde arıza tespiti, kök neden, hafifletme | 48 problem (arXiv), iki DeathStarBench uygulaması | Konteynerli mikroservis; arıza enjeksiyonu; MIT lisans | Düşük: tek uygulama ortamı; sunucu filosu ve adminlik işi yok | Ajan API'leri: log/metrik al, kabuk komutu çalıştır |
| ITSMBench (Atomicwork + New Measure) | BT servis yönetimi ve BT operasyon görevleri; deterministik doğrulayıcı | 89 uzman görev (arama özeti) | Ortam durumu üzerinden doğrulama | Orta: operasyon görevleri var, ama bilet/ITSM ağırlıklı; çok sunucu dağıtımı ağırlıklı değil | En iyi skor ~%46 Pass@1 (kısmi tablo, doğrulanmadı) |
| OpsEval (Tsinghua, 2023, güncel 2025) | BT operasyon bilgisi: çoktan seçmeli ve kısa cevap | 7.184 çoktan seçmeli + 1.736 kısa cevap | Metin tabanlı; EN/ZH; GitHub: NetManAIOps | Çok düşük: eylem yok, yalnızca bilgi sorusu | Aracı görev değil, yanıt kalitesi ölçülür |
| Terminal-Bench 2.0 (ICLR 2026) | Konteyner içi zor terminal görevleri | 89 görev (229 aday arasından seçildi) | Her görev için konteyner, test ve referans çözüm | Orta-düşük: tek makine, filo yok; ama terminal ve doğrulama modeli bizim bench için iyi bir şablon | En iyi sonuç ~%63 (arama özeti) |
| InterCode / NL2Bash (NeurIPS 2023) | Etkileşimli bash; dosya sistemi değişikliğinin gold komutla karşılaştırılması | Bash parçasında 200 ila ~700 görev (kaynaklar çelişiyor, doğrulanmadı) | Ubuntu konteyneri | Düşük: tek kabuk, tek makine | Doğrulama fikri (dosya sistemi durumu) bizim için faydalı |
| OSWorld (2024; OSWorld-Verified 2025) | Gerçek masaüstü ve web görevleri, GUI ajanı | 369 görev (+43 Windows analiz görevi); 8 Drive görevi çıkarılabilir | VM, GUI | Çok düşük: GUI tabanlı, sunucu filosu değil | İnsan ~%72, en iyi model ilk yayında ~%12 |
| Windows Agent Arena (Microsoft, 2024) | Windows masaüstü görevleri | 154 görev (orijinal); V2 141 görev; resmi sayfa 150+ diyor | Windows VM, Azure paralel değerlendirme | Düşük: GUI; ama Windows odaklı olması ilgi çekici | V2'de "infeasible" görevler ayıklandı (özet) |
| IaC-Eval (NeurIPS 2024) | Bulut IaC kod üretimi (AWS, Terraform benzeri) | 458 senaryo | Kod üretimi; niyet spesifikasyonu ile kontrol | Düşük: kod üretir, çalıştırmaz; Ansible görevi yok | GPT-4 pass@1 ~%19 (özet). Ansible için ayrı Ansible Wisdom çalışması var, ama bu bir bench değil |
| Multi-IaC-Eval (2025) | CloudFormation, Terraform, CDK | Doğrulanmadı | IaC kodu | Düşük: Ansible yok | IaC-Eval'in genişletmesi |
| DevOps-Gym (ICLR 2026, arXiv 2601.20882) | Build ve yapılandırma, izleme, sorun çözme, test üretimi; Java ve Go projeleri | 700+ görev, 30+ proje (PDF'te pipeline sayısı 14 gibi görünüyor, doğrulanmadı) | Proje depoları | Düşük-orta: yazılım DevOps'u; sunucu filosu adminliği değil | Açık kaynak olacağı söylendi |
| SWE-bench (ICLR 2024) ailesi | GitHub issue çözümü; testler geçmeli | Tam 2.294; Verified 500; Live 1.319 (özet) | Python repoları | Çok düşük: kod yaması, sistem yönetimi değil | Metodolojik şablon olarak (testle doğrulama) değerli |
| Cybench (Stanford, ICLR 2025) | CTF siber güvenlik görevleri | 40 görev, 17'sinde alt görev | Kali benzeri konteyner | Çok düşük | Zor görevlerde en iyi model ~%17-29 |
| SOP-Bench (Amazon, arXiv 2506.08119) | Uzman SOP'larını takip etme | 2.000+ görev, 12 alan | Sektör SOP'ları (sağlık, lojistik, finans vb.) | Orta kavramsal: runbook mantığı var; BT adminliği değil | Runbook yürütme tasarımı için ilham |
| NetLLMeval | Ağ yönetimi görevleri; canlı ağ emülasyonu | Doğrulanmadı | Ağ emülasyonu | Düşük-orta: yönetim görevleri, ama ağ cihazları | Otomatik temel doğruluk fikri |
| Toward Agentic SysAdmin (arXiv 2606.26960) | Sistem yönetiminde ajan kavramsal tartışması | Bilinmiyor | Bilinmiyor | Olası ilgi; içeriği okunamadı | Yalnızca referans listesi alındı; içerik doğrulanmadı |
| sysadmin-env, RunbookOps (topluluk projeleri) | Linux düzeltme ortamı; 15 deterministik runbook vakası | 15 (RunbookOps) | Küçük ölçekli | Düşük-orta: runbook fikri | Hobi/yarışma projesi; güvenilirlik doğrulanmadı |

## Bulgular

1. Boşluk var. Arama sonuçlarında, çok sunuculu filo düzeyinde adminlik işini (aynı komutu hedef gruba dağıtma, sunucu başına sonuç toplama, kısmi başarısızlıkta yeniden deneme, kurulum ve doğrulama, sonuç raporu veya e-posta) doğrudan ölçen herkese açık bir bench bulunamadı.
2. En yakın olanlar: ITBench ve ITSMBench (operasyon görevleri, deterministik ya da sonuç bazlı doğrulama), Terminal-Bench 2.0 (zor komut satırı görevleri ve doğrulama şablonu), AIOpsLab (ajan ile ortam arasında API tabanlı yürütme). Hiçbiri birden çok sunucuya dağıtılan iş akışını değerlendirmiyor.
3. Ansible ya da IaC tarafında (IaC-Eval, Multi-IaC-Eval) kod üretimi ölçülüyor, dağıtılmış çalıştırma ve sonucu doğrulama ölçülmüyor. Bu bizim hedefimizle örtüşmüyor.
4. sunucu/akış'ya özgü herkese açık bir bench bulunamadı. Bu aramada OpenText forumuna erişilemedi (404 ve yönlendirme sorunu), bu yüzden bu sonuç "bulunamadı" anlamına geliyor; "yok" anlamına gelmiyor.
5. Tasarım için alınabilecek fikirler: Terminal-Bench ve InterCode'daki durum kontrolü (dosya sistemi ya da çıktı karşılaştırma), AIOpsLab'daki ajan-ortam API ayrımı, SOP-Bench'teki adım adım runbook izleme, ITSMBench'teki "erken durma" ve "kanıtsız işlem" hata modları (özet kaynaklı).

## Kaynaklar

- ITBench: https://www.research.ibm.com/blog/it-agent-benchmark ; https://huggingface.co/blog/ibm-research/itbench-aa ; https://github.com/ibm/itbench
- AIOpsLab: https://arxiv.org/abs/2501.06706 ; https://www.microsoft.com/en-us/research/blog/aiopslab-building-ai-agents-for-autonomous-clouds/
- ITSMBench: https://www.atomicwork.com/itsm-bench
- OpsEval: https://arxiv.org/abs/2310.07637
- Terminal-Bench: https://arxiv.org/abs/2601.11868
- InterCode: https://arxiv.org/pdf/2306.14898
- OSWorld: https://os-world.github.io
- Windows Agent Arena: https://microsoft.github.io/WindowsAgentArena
- IaC-Eval: https://neurips.cc/virtual/2024/poster/97835 ; Multi-IaC-Eval: https://arxiv.org/html/2509.05303v1
- DevOps-Gym: https://arxiv.org/abs/2601.20882
- SWE-bench: https://epoch.ai/benchmarks/swe-bench-verified
- Cybench: https://crfm.stanford.edu/2024/08/19/cybench.html
- SOP-Bench: https://arxiv.org/abs/2506.08119
- Toward Agentic SysAdmin: https://arxiv.org/pdf/2606.26960
- sunucu otomasyonu belgeleri (ilgili): https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/script_execution/RunningaServerScriptSavedScriptorAdHocScript.htm
