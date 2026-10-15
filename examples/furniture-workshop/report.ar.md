<div dir="rtl">

# ملف الأدلة: Örnek Mobilya Atölyesi

- **المنشأة:** Örnek Mobilya Atölyesi
- **وضع التحليل:** self
- **أساس التفويض:** owner (synthetic example)
- **ملف التشغيل:** sop-replication
- **تاريخ الإصدار:** 2026-10-15

> يعرض هذا الملف ما تُظهره الأدلة المسجّلة، مع درجة لكل نتيجة. وهو ليس تدقيقاً ولا تقييماً ولا استشارة قانونية ولا ضماناً. كل ما لم يُغطَّ أدناه مجهول، وليس غير موجود.

## كيف تُقرأ الدرجات

- **A**: سجل جرى التحقق منه لدى الجهة المُصدِرة، أو التُقط مباشرة، أو من طرف ثالث مستقل
- **B**: وثيقة حاكمة أو سجل عام أو طرف ثالث
- **C**: سجل سلّمته المنشأة نفسها
- **D**: شهادة شخص واحد أو مؤشر عام
- **E**: استنتاج المحلل

## التغطية حسب الطبقة

| الطبقة | الادعاءات | أفضل درجة | مجهولات مفتوحة |
|---|---|---|---|
| الاستراتيجية | 0 | — (لا أدلة) | 0 |
| الإيراد والتسعير | 2 | C | 0 |
| رحلة العميل | 0 | — (لا أدلة) | 0 |
| العمليات | 3 | A | 1 |
| المكائن وخطوط الإنتاج | 0 | — (لا أدلة) | 0 |
| الأنظمة والبيانات | 0 | — (لا أدلة) | 0 |
| الناس والتوظيف | 0 | — (لا أدلة) | 0 |
| التوريد | 0 | — (لا أدلة) | 0 |
| المالية والتكاليف | 0 | — (لا أدلة) | 1 |
| التراخيص والوضع القانوني | 0 | — (لا أدلة) | 1 |
| الثقافة والمعرفة الضمنية | 1 | D | 0 |

## قائمة ملف التشغيل

| البند | المطلوب | أفضل درجة | الحالة |
|---|---|---|---|
| ما العملية الأساسية من الطلب إلى التسليم كما تُنفَّذ فعلاً، بما فيها الاستثناءات؟ | B | C | متعارض |
| أي خطوة تحدّ من الطاقة الإنتاجية، وبكم؟ | B | A | مستوفى |
| ما المكائن الموجودة وطاقتها الاسمية وحالتها ومن يستطيع تشغيلها؟ | B | — | غير مغطّى |
| ماذا يفعل كل دور فعلياً، ومن يقرر ماذا، ومن هو نقطة الفشل الوحيدة؟ | C | — | غير مغطّى |
| كيف يتم التوظيف والتهيئة والتدريب والدفع؟ | C | — | غير مغطّى |
| من الموردون الحرجون وما مُدد التوريد والبدائل؟ | B | — | غير مغطّى |
| كم تكلفة الوحدة أو الطلب الواحد (مواد، دقائق عمل × أجر، مصاريف عامة) وكم هامشها؟ | B | — | غير مغطّى |
| من أين يأتي الإيراد (العملاء، القنوات، التركّز) وكيف يُحدَّد السعر؟ | B | C | أقل من الدرجة المطلوبة |
| ما الأدوات والأنظمة التي تحفظ البيانات (بما فيها الورق وواتساب وإكسل) وكيف تنتقل المعلومات؟ | C | — | غير مغطّى |
| ما التراخيص والتصاريح والتسجيلات المطلوبة وهل هي سارية؟ | B | — | غير مغطّى |
| ما المعرفة الموجودة فقط في رؤوس الناس، وعند من؟ | C | D | أقل من الدرجة المطلوبة |

## النتائج

### الإيراد والتسعير

- **[C]** Revenue is spread across a small number of customers (see concentration). — مصدر واحد (أو مصادر تحت جهة واحدة) · `ev_b18517dfe1b9`

### العمليات

- **[A]** The spray booth is the bottleneck: the longest wait in the process is before or in painting. — مثلَّث (مصدران مستقلان أو أكثر) · `ev_4df8e4bba69b`, `ev_be6db0c90b5f`, `ev_b03afcb70334`
- **[C]** The written procedure and the usta state a lead time of about 10 days. — مصدر واحد (أو مصادر تحت جهة واحدة) · `ev_1b9f9e9922ad`, `ev_4fa429b9c6c4`
- **[C]** Order-to-delivery takes a median of 14.9 days in the orders group (p90 18.4 days). — مصدر واحد (أو مصادر تحت جهة واحدة) · `ev_4df8e4bba69b`

### الثقافة والمعرفة الضمنية

- **[D]** Edge-bander setup for 2 mm PVC depends on a single operator. — مصدر واحد (أو مصادر تحت جهة واحدة) · `ev_b3dde0d62d97`, `ev_67129ffc8cf8`

## التعارضات (المُعلَن مقابل الفعلي)

- Why does the stated lead_time_days (10 days) differ from the enacted lead_time_days (14.9 days)? (`unk_0b07fd610764`)

## المجهولات المفتوحة

- What is the unit cost of a kitchen cabinet (materials, labour minutes, overhead)? (`unk_cd0137391d58`, open) · يحتاج: system_record · الخطوة التالية: Collect purchase e-invoices for boards and edge tape for the same 3 months
- Which licences and permits does the workshop hold? (`unk_379196879fe2`, open) · يحتاج: public_record · الخطوة التالية: Pull the trade registry entry and municipal licence

## تخمين: غير مدعوم بأدلة مسجّلة

- ⚠ Customers mostly come through architects' referrals.

## قابلية النسخ

**يحتاج أصلاً (رخصة، موقع، رأس مال، معدات)**

- The spray booth is the bottleneck: the longest wait in the process is before or in painting.

**يحتاج بناء قدرة**

- Edge-bander setup for 2 mm PVC depends on a single operator.

**قابل للتدوين (يمكن كتابته وتعليمه)**

- Order-to-delivery takes a median of 14.9 days in the orders group (p90 18.4 days).

## التزامات إعادة البناء

**open** · {'open': 3, 'unknown': 6}

- `ops.core-process` — **open** — missing owner (accountable role); missing case evidence: happy_path, exception_rework, peak_load, staff_absence, supplier_failure; missing passing verifier; open unknowns on this item
- `ops.bottleneck` — **open** — case evidence below grade B: happy_path, peak_load
- `equip.register` — **unknown** — no evidence recorded for this item
- `people.roles` — **unknown** — no evidence recorded for this item
- `people.hiring` — **unknown** — no evidence recorded for this item
- `supply.suppliers` — **unknown** — no evidence recorded for this item
- `econ.unit-cost` — **unknown** — no evidence recorded for this item
- `systems.map` — **unknown** — no evidence recorded for this item
- `culture.tacit` — **open** — missing owner (accountable role); missing case evidence: staff_absence; missing passing verifier

## ملحق الأدلة

- `ev_1b9f9e9922ad` **[C]** The written procedure states a standard lead time of 10 days. — المصدر: sop.md (الحيازة: subject_held), governing_document · الموضع: line 12
- `ev_4df8e4bba69b` **[C]** Process discovered from 24 cases / 177 events: median cycle time 357.0h (p90 441.0h); most common path order → measure → cut → edge → assembly → paint → deliver (15 cases); 9 cases with rework. — المصدر: WhatsApp Chat - Siparisler.txt (الحيازة: subject_held), system_record · القيود: Events reconstructed from message keywords: steps never mentioned in this chat are missing.; Activity mapping was supplied by the analyst; different keywords give a different process.
- `ev_4fa429b9c6c4` **[D]** The usta says a typical order takes about ten days. — المصدر: interview-usta.txt (الحيازة: captured_live), testimony · الموضع: line 4
- `ev_67129ffc8cf8` **[D]** A chat message says only one person can set up the edge-bander for 2 mm PVC. — المصدر: WhatsApp Chat - Siparisler.txt (الحيازة: subject_held), testimony · الموضع: chat
- `ev_b03afcb70334` **[A]** Nine assembled carcasses were waiting in front of the single spray booth. — المصدر: Site walk 2026-10-10 (الحيازة: captured_live), direct_observation · الموضع: workshop floor · القيود: Observed workers may behave differently while observed (Hawthorne effect).
- `ev_b18517dfe1b9` **[C]** 8 sales invoices, 4 counterparties, total 351600.0 TRY; largest counterparty share 0.355; HHI 3014. — المصدر: invoice-001.xml (الحيازة: subject_held), system_record · القيود: Covers only the invoices ingested; missing months or off-book sales are not represented.; Counterparties are identified by tax id. Check related parties separately.
- `ev_b3dde0d62d97` **[D]** Only one operator can set up the edge-bander for 2 mm PVC. — المصدر: interview-usta.txt (الحيازة: captured_live), testimony · الموضع: line 7
- `ev_be6db0c90b5f` **[D]** The usta names the single spray booth as where orders get stuck. — المصدر: interview-usta.txt (الحيازة: captured_live), testimony · الموضع: line 10


</div>
