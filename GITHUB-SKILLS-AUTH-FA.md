# مهارت‌ها و ماژول ورود JobLink

## ۱۰ مهارت ترکیبی پیشنهادی برای ثبت‌نام کارجو

| # | مهارت | Turkish/English | دسته |
|---:|---|---|---|
| 1 | پایتون | Python | نرم‌افزار و AI |
| 2 | جاوااسکریپت/تایپ‌اسکریپت | JavaScript / TypeScript | وب |
| 3 | SQL و طراحی پایگاه داده | SQL / Database | داده |
| 4 | Git و GitHub | Git / GitHub | توسعه تیمی |
| 5 | Docker و Linux | Docker / Linux | DevOps |
| 6 | LLM، RAG و AI Agent | LLM / RAG / AI Agent | هوش مصنوعی |
| 7 | ترکی استانبولی | Türkçe | کار در ترکیه |
| 8 | ارتباط با مشتری و فروش | Müşteri Hizmetleri / Satış | خدمات |
| 9 | ایمنی و بهداشت کار | İş Sağlığı ve Güvenliği | خدمات و تولید |
| 10 | اجازه کار و قرارداد ترکیه | Çalışma İzni / İş Sözleşmesi | مهاجرت کاری |

## منابع GitHub بررسی‌شده

- [G4brym/authentication-using-d1-example](https://github.com/G4brym/authentication-using-d1-example) — نمونه Register/Login برای Cloudflare Workers + D1 با Hono؛ شامل `POST /api/auth/login` و session.
- [leopoldsw/cloudflare-auth](https://github.com/leopoldsw/cloudflare-auth) — کیت کامل‌تر برای ایمیل/رمزعبور، magic link، تأیید ایمیل، reset password و session امن D1.
- [gr2m/cloudflare-worker-github-oauth-login](https://github.com/gr2m/cloudflare-worker-github-oauth-login) — نمونه OAuth ورود با GitHub روی Worker.

## تصمیم امنیتی JobLink

از کپی مستقیم کد ناشناخته یا قراردادن Client Secret در GitHub خودداری می‌کنیم. برای نسخه تولیدی:

1. ثبت‌نام و ورود در Cloudflare Worker انجام شود.
2. کاربر در D1 ذخیره شود.
3. رمز عبور فقط به شکل hash ذخیره شود.
4. session در cookie امن و HttpOnly باشد.
5. `GITHUB_CLIENT_SECRET` و `AUTH_SECRET` فقط با `wrangler secret put` تنظیم شوند.
6. شماره تلفن پیش‌فرض خصوصی بماند.
7. ثبت‌نام با رضایت KVKK/GDPR انجام شود.
8. نقش‌ها: jobseeker، employer، admin.
9. ورود GitHub اختیاری باشد؛ GitHub رمز عبور JobLink را دریافت نمی‌کند.
10. قبل از deploy، D1 ID و دامنه رسمی باید مشخص شود.

## وضعیت فعلی

- مهارت‌ها در سیستم matching فعلی قابل استفاده‌اند.
- تست ربات و مچینگ محلی موفق است.
- منابع GitHub شناسایی شدند.
- ماژول Login هنوز به Cloudflare production وصل نشده، چون D1 ID، OAuth Client ID/Secret و AUTH_SECRET ارائه نشده است.
- هیچ secret در workspace ذخیره نشده است.
