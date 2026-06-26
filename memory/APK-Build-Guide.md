# 📱 NaBaB APK তৈরি ও Share করার গাইড

> **এই মুহূর্তে NaBaB একটি পূর্ণাঙ্গ PWA (Progressive Web App)** — যেটি Android-এ APK হিসেবে install করা ও শেয়ার করা যায় Play Store ছাড়াই।

---

## 🎯 ৩টি পদ্ধতি — সবচেয়ে সহজ থেকে কঠিন পর্যন্ত

### 🥇 পদ্ধতি ১: PWABuilder দিয়ে APK তৈরি (সবচেয়ে সহজ, ২ মিনিট)

এটি Microsoft-এর free tool — কোনো Android Studio লাগে না। **শুধু URL দিন, APK পেয়ে যান।**

#### ধাপসমূহ:

1. ব্রাউজারে যান → **[https://www.pwabuilder.com](https://www.pwabuilder.com)**

2. URL ঘরে নিজের প্ল্যাটফর্মের লিংক দিন:
   ```
   https://ai-bangladesh.preview.emergentagent.com
   ```
   (Production-এ deploy হলে আপনার custom domain যেমন `nabab.app` দেবেন)

3. **"Start"** বাটনে ক্লিক করুন। PWABuilder আপনার PWA scan করবে — সবুজ checkmark গুলো দেখাবে (NaBaB-এ সব ✅ পাশ করবে — manifest, icons, service worker সব ready)।

4. উপরের **"Package For Stores"** বাটনে ক্লিক করুন → **"Android"** কার্ডে **"Generate Package"** এ ক্লিক করুন।

5. একটি form আসবে — আগে থেকে পূরণ করা থাকবে। নিচের ঘরগুলো verify/edit করুন:
   - **Package ID:** `app.nabab.bd` (recommended) অথবা `com.nabab.app`
   - **App name:** `NaBaB`
   - **Launcher name:** `NaBaB`
   - **Version code:** `1`
   - **Version name:** `1.0.0`
   - **Display mode:** `standalone`
   - **Orientation:** `portrait` (already in manifest)
   - **Signing key:** **"New"** select করুন (PWABuilder নিজেই signing key বানিয়ে দেবে — pass remember করতে হবে)
     - **Key alias:** `nabab-key`
     - **Key password / Keystore password:** আপনার পছন্দমতো (এটা মনে রাখবেন — পরের update-এও লাগবে)
     - **Country code:** `BD`
     - **Full name:** `G.K.M. Jarif Ur Rahim`
     - **Organization:** `NaBaB`
     - **City:** `Jashore`

6. **"Download Package"** ক্লিক করুন — একটি `.zip` ফাইল download হবে।

7. Zip-এর ভিতরে দুটি ফাইল পাবেন:
   - **`app-release-signed.apk`** ← এটিই **শেয়ার করার APK**
   - **`signing.keystore`** + readme — এটি **সংরক্ষণ করুন** (Play Store-এ upload করতে বা পরের version বানাতে কাজে লাগবে)

8. APK ফাইলটি Google Drive / WhatsApp / Telegram / Bluetooth দিয়ে যেকোনো Android-এ পাঠান।

#### Install করতে:
- Android-এ APK ফাইল ট্যাপ করুন
- প্রথমবার **"Install from unknown sources"** allow করতে হবে (Settings → Apps → আপনার যে অ্যাপ দিয়ে খুলেছেন সেটার permission)
- Install শেষ হলে home screen-এ **NaBaB** আইকন দেখাবে — open করলে full-screen native-style app খুলবে!

---

### 🥈 পদ্ধতি ২: Chrome-এ "Add to Home Screen" (APK ছাড়া, instant)

ব্যবহারকারীদের সবচেয়ে দ্রুত instruction দিতে চান? এটিই সহজ:

1. Android Chrome-এ যান → [https://ai-bangladesh.preview.emergentagent.com](https://ai-bangladesh.preview.emergentagent.com)
2. উপরের ৩-ডট মেনু → **"Add to Home screen"** / **"Install app"**
3. নাম confirm করুন → Install
4. Home screen-এ NaBaB icon দেখাবে — exact native app-এর মতো দেখতে ও চলে।

**Benefit:** কোনো "unknown sources" permission লাগে না, এক ক্লিকে install, automatic updates।
**Drawback:** WhatsApp/file দিয়ে share করা যায় না, শুধু URL share করতে হয়।

---

### 🥉 পদ্ধতি ৩: Bubblewrap CLI (Advanced — local Android SDK লাগে)

যদি আপনার নিজের ল্যাপটপে Android Studio install করা থাকে:

```bash
npm i -g @bubblewrap/cli
bubblewrap init --manifest https://ai-bangladesh.preview.emergentagent.com/manifest.json
bubblewrap build
```

এতে `app-release-signed.apk` তৈরি হবে। **আমাদের cloud container-এ Android SDK নেই বলে এটা এখান থেকে করা যাচ্ছে না** — তবে আপনি লোকাল ল্যাপটপে চাইলে করতে পারবেন।

---

## ⚠️ গুরুত্বপূর্ণ Notes

### TWA (Trusted Web Activity) সম্পর্কে:
PWABuilder যে APK বানাবে সেটি **TWA** technology ব্যবহার করে — Google-এর official সমাধান যা **Chrome browser-কে full-screen app হিসেবে wrap করে।** এটি একটি প্রকৃত native Android app হিসেবে দেখায়, Play Store-এ আপলোড করা যায়, এবং performance native-এর কাছাকাছি।

### Domain Verification:
TWA সঠিকভাবে কাজ করতে হলে একটি ছোট কনফিগ লাগে — Digital Asset Links (assetlinks.json)। PWABuilder যে zip দেবে তাতে একটি `assetlinks.json` থাকবে যা আপনার domain-এ deploy করতে হবে:

```
https://ai-bangladesh.preview.emergentagent.com/.well-known/assetlinks.json
```

**পর্যাপ্ত verification না থাকলে:** APK খুললে উপরের bar-এ URL দেখাবে (Chrome custom tab look)।
**Verified হলে:** Bar উধাও হবে, সম্পূর্ণ native app দেখাবে।

বললে আমি `assetlinks.json` route-টিও সেট করে দিতে পারি (sha256 fingerprint লাগবে যা PWABuilder-এর জেনারেট হওয়া keystore থেকে নিতে হবে)। এটি optional — APK এমনিতেই চলবে।

### Production Domain:
এখন আপনার URL `ai-bangladesh.preview.emergentagent.com` — preview domain। Production-এ যাওয়ার সময়:
- নিজের domain কিনুন (যেমন `nabab.app` ~ ৳১৫০০/বছর)
- Vercel/Cloudflare-এ deploy করুন (Phase C-তে আমরা এটি automate করব)
- ওই custom domain দিয়ে PWABuilder-এ APK regenerate করুন
- তাহলে APK-এ আপনার নিজের domain দেখাবে — professional!

---

## ✅ Quick Checklist (এখনই করতে পারেন)

- [ ] PWABuilder.com খুলুন
- [ ] URL: `https://ai-bangladesh.preview.emergentagent.com`
- [ ] Package ID: `app.nabab.bd`
- [ ] Signing key: New (password মনে রাখুন)
- [ ] APK download করুন
- [ ] WhatsApp/Telegram-এ ৫-১০ জন বন্ধুকে পাঠান feedback-এর জন্য

**~১০ মিনিটে আপনি একটি shareable APK পেয়ে যাবেন।**

---

## 🎁 Bonus: যা আপনি পরে চাইলে আমি বানিয়ে দিতে পারি

- 📝 **Beta tester feedback form** (Google Form integration)
- 📊 **In-app analytics** (PostHog / Plausible)
- 🔔 **Web push notifications** (যখন admin credit approve করবেন)
- 🎯 **Custom install prompt** (chrome auto-prompt enhance)
- 📱 **Android-specific UI tweaks** (safe area, status bar color)
- 🏪 **Play Store listing copy** (Bangla + English, screenshots, feature graphic)

বললে যেকোনোটা যোগ করে দেব।
