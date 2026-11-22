/**
 * يستقبل نماذج موقع raqam.site ويحفظها في جدول «رقم | طلبات الموقع».
 * - طلبات المعلنين  → تبويب «الطلبات» + إيميل تنبيه لصاحب الجدول
 * - اشتراكات النشرة → تبويب «المشتركون» (بدون تكرار نفس البريد)
 */
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function doPost(e) {
  const p = (e && e.parameter) || {};
  if (p.website) return ok_();                       // خانة مخفية: سبام
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const email = clean_(p.email).toLowerCase();
    if (!EMAIL_RE.test(email)) return ok_();

    if (p.form === 'news') {
      const sh = ss.getSheetByName('المشتركون');
      const last = sh.getLastRow();
      const emails = last > 1 ? sh.getRange(2, 2, last - 1, 1).getValues().flat().map(v => String(v).toLowerCase()) : [];
      if (emails.indexOf(email) === -1) sh.appendRow([new Date(), email, clean_(p.page), 'نشط']);
    } else {
      const company = clean_(p.company);
      if (!company) return ok_();
      const type = clean_(p.type);
      ss.getSheetByName('الطلبات').appendRow([new Date(), company, email, type, clean_(p.page), 'جديد', '']);
      MailApp.sendEmail({
        to: Session.getEffectiveUser().getEmail(),
        subject: 'طلب إعلان جديد من raqam.site: ' + company,
        body: 'الجهة: ' + company + '\nالبريد: ' + email + '\nنوع الإعلان: ' + type +
              '\n\nكل الطلبات في الجدول:\n' + ss.getUrl()
      });
    }
  } finally {
    lock.releaseLock();
  }
  return ok_();
}

// يقص النص الطويل، ويمنع تنفيذ أي نص يبدأ كمعادلة داخل الجدول
function clean_(v) {
  v = String(v || '').trim().slice(0, 300);
  return /^[=+\-@]/.test(v) ? "'" + v : v;
}

function ok_() {
  return ContentService.createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}
