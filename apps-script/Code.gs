/**
 * يستقبل نماذج موقع raqam.site ويحفظها في جدول «رقم | طلبات الموقع».
 * - طلبات المعلنين  → تبويب «الطلبات» + إيميل تنبيه لصاحب الجدول
 * - اشتراكات النشرة → تبويب «المشتركون» (بدون تكرار)
 * - فتح الرابط مباشرة (doGet) يعرض فحصًا سريعًا لعدد الطلبات والمشتركين.
 */
const SHEET_ID = '144v-2ns7otnTSYBaZihdfVnJ8ckQXXsGt3a130rEiTY';
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function doGet() {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  return json_({ ok: true, sheet: ss.getName(),
    requests: ss.getSheetByName('الطلبات').getLastRow() - 1,
    subscribers: ss.getSheetByName('المشتركون').getLastRow() - 1 });
}

function doPost(e) {
  const p = (e && e.parameter) || {};
  if (p.website) return json_({ ok: true });
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const ss = SpreadsheetApp.openById(SHEET_ID);
    const email = clean_(p.email).toLowerCase();
    if (!EMAIL_RE.test(email)) return json_({ ok: false });
    if (p.form === 'news') {
      const sh = ss.getSheetByName('المشتركون');
      const last = sh.getLastRow();
      const emails = last > 1 ? sh.getRange(2, 2, last - 1, 1).getValues().flat().map(v => String(v).toLowerCase()) : [];
      if (emails.indexOf(email) === -1) sh.appendRow([new Date(), email, clean_(p.page), 'نشط']);
    } else {
      const company = clean_(p.company);
      if (!company) return json_({ ok: false });
      const type = clean_(p.type);
      ss.getSheetByName('الطلبات').appendRow([new Date(), company, email, type, clean_(p.page), 'جديد', '']);
      MailApp.sendEmail({
        to: Session.getEffectiveUser().getEmail(),
        subject: 'طلب إعلان جديد من raqam.site: ' + company,
        body: 'الجهة: ' + company + '\nالبريد: ' + email + '\nنوع الإعلان: ' + type + '\n\nكل الطلبات:\n' + ss.getUrl()
      });
    }
  } finally { lock.releaseLock(); }
  return json_({ ok: true });
}

function clean_(v) {
  v = String(v || '').trim().slice(0, 300);
  return /^[=+\-@]/.test(v) ? "'" + v : v;
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
