# Kira from Astra

Kira — macOS uchun ovozli va AI yordamchi. U ekraningizdagi narsani ko'rsatishingiz, savol berishingiz, kalendar bilan ishlashingiz va fon agentlarini boshqarishingiz mumkin.

## Asosiy imkoniyatlar

- **Ovoz va chat:** savolni yozing yoki ayting, javobni Kira ovozli o'qib beradi.
- **Point at your screen:** ekrandagi narsani belgilang (aylana chizing, bosing yoki chizib qo'ying), so'ngra savolingizni yozing yoki ayting. Kira belgilangan joyni ko'radi.
- **Kalendar:** "Move my dentist appointment to 4." kabi so'rovlar bilan voqealarni boshqaring. Adding is immediate; moving or deleting asks first.
- **Fon agentlari:** uzoq vazifalarni fonda bajartiring va natijasini keyinroq ko'ring.
- **Yig'ilishlar va diktovka:** yig'ilish xulosasi va matnni ovoz orqali kiritish.

## O'rnatish

Talablar: macOS 26 yoki undan yangi, Xcode Command Line Tools.

1. Manba kodni yuklab oling va papkani `KIRA_DIR` orqali ko'rsating (standart: `~/.kira`).
2. `install.sh` ni ishga tushiring. U `build.sh` orqali Kira ni quradi va `~/Applications/Kira.app` ga o'rnatadi.
3. Kira ochilgach, sozlash oynasi qolgan qadamlarni ko'rsatadi.

Nix orqali o'rnatish uchun `flake.nix` dan foydalaning.

## Yangilanishlar

Nix orqali o'rnatilgan bo'lsa, Settings'da "Updates are managed by Nix" yozuvi chiqadi. Yangilash uchun `nix profile upgrade` yoki `nix run` ni qayta ishga tushiring.

## Ruxsatlar

Kira ishlashi uchun macOS ruxsatlari kerak bo'ladi: mikrofon, nutni tanish, ekranni yozib olish, Accessibility, kalendar va Automation. Har bir ruxsat faqat o'z vazifasi uchun so'raladi. Kalendar ruxsati Kira ga kalendarni o'qish va so'ralgan voqealarni qo'shish imkonini beradi.

## Mualliflik

Muallif: **Xasan Abdukhafizov**

Copyright © 2026 Xasan Abdukhafizov.

Mualliflik qaydi: AUTHORS.md va COPYRIGHT. Uchinchi tomon huquqlari ushbu qayd bilan o‘zgarmaydi.
