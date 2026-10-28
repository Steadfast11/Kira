// Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
// One source for setup (boot.html) and Settings: the languages, the hearing / speaking / AI providers, the permissions, the
// connector choices, the on-Mac models and which one fits this Mac, and every line of interface copy in each interface language.
// Data and small pure functions only: each page draws them in its own style. A classic script: loadPage() inlines it (the CATALOG marker).
const KIRA = (() => {
  // ---- Interface languages. English is complete; a missing key in another language falls back to it. To add one: a new block.
  const UI = ['en', 'uz', 'ru'];
  const STRINGS = {
    en: {
      'chrome.skipIntro': 'Skip intro', 'boot.cta': 'Set up Kira', 'chrome.mute': 'Turn sound off', 'chrome.unmute': 'Turn sound on',
      'common.back': 'Back', 'common.next': 'Continue', 'common.skip': 'Skip for now', 'common.test': 'Test', 'common.testing': 'Testing…',
      'common.works': 'Works', 'common.saved': 'Saved in Keychain', 'common.keyPh': 'Paste your API key', 'common.getKey': 'Get a key',
      'common.model': 'Model', 'common.voice': 'Voice', 'common.sample': 'Play a sample', 'common.recommended': 'Recommended', 'common.free': 'Free',
      'common.install': 'Install', 'common.signIn': 'Sign in', 'common.use': 'Use', 'common.inUse': 'In use', 'common.remove': 'Remove key',
      'common.download': 'Download', 'common.pause': 'Pause', 'common.resume': 'Resume', 'common.delete': 'Delete', 'common.checking': 'Checking…',
      'common.address': 'Address', 'common.steps': 'Setup steps', 'common.step': 'Step {n} of {total}',
      'name.first': 'First name', 'name.last': 'Last name (optional)', 'name.go': 'Continue', 'name.skip': 'Skip',
      'name.say': 'Say it differently', 'name.sayPh': 'How to say it, e.g. “Ha-san”',
      'greet.named': 'Hi {name}, great to meet you!', 'greet.none': 'Hi there, great to meet you!',
      'lang.title': 'What language do you speak?', 'lang.sub': 'Kira will listen, speak and answer in it. Pick more than one if you switch.',
      'lang.search': 'Search languages', 'lang.primary': 'Primary', 'lang.makePrimary': 'Make primary', 'lang.none': 'No language matches “{q}”.',
      'lang.ui': 'Kira’s menus in', 'lang.hears': 'Apple hears it', 'lang.speaks': 'Kira speaks it',
      'lang.hearApple': 'Apple listens in {lang} on this Mac.', 'lang.hearNo': 'Apple can’t listen in {lang} on this Mac. Next, pick Whisper or a cloud voice.',
      'lang.hearLoad': 'Apple’s {lang} speech model downloads when you continue.',
      'lang.speakKokoro': 'Kira speaks {lang} with its own voice, on this Mac.', 'lang.speakMac': 'Kira speaks {lang} with a Mac voice.',
      'lang.speakNo': 'No voice on this Mac speaks {lang} yet: Kira answers in text, or pick a cloud voice next.',
      'acct.title': 'Save your setup', 'acct.sub': 'An account keeps Kira’s settings on all your Macs.', 'acct.email': 'Email',
      'acct.continue': 'Continue with Email', 'acct.google': 'Continue with Google', 'acct.skip': 'Continue without an account',
      'acct.soon': 'Accounts aren’t available yet. Everything works without one.',
      'voice.title': 'How should Kira hear and speak?', 'voice.hear': 'Hearing', 'voice.speak': 'Speaking',
      'voice.data': 'Apple, Whisper and Kokoro keep everything on this Mac. A cloud provider gets your voice (hearing) or Kira’s replies (speaking) only while you use Kira. Keys stay in your Mac’s Keychain, never in files or logs.',
      'voice.fallback': 'If a provider fails, Kira falls back to Apple and Kokoro.',
      'prov.apple': 'Apple, on this Mac', 'prov.apple.note': 'Free, no key. Your voice never leaves this Mac.',
      'prov.deepgram': 'Deepgram', 'prov.deepgram.hear': 'Nova: fast and accurate, in many languages.', 'prov.deepgram.speak': 'Aura: natural voices, quick to start.',
      'prov.openai': 'OpenAI', 'prov.openai.hear': 'Transcription, paid per minute.', 'prov.openai.speak': 'Natural voices, paid per character.',
      'prov.elevenlabs': 'ElevenLabs', 'prov.elevenlabs.speak': 'Expressive voices in many languages.',
      'prov.custom': 'Custom server', 'prov.custom.note': 'Any OpenAI-compatible speech API.',
      'prov.whisper': 'Whisper, on this Mac', 'prov.whisper.note': 'Free and private. Downloads a model once.',
      'prov.kokoro': 'Kokoro, on this Mac', 'prov.kokoro.note': 'Free and private. Kira’s own voice.',
      'prov.system': 'Mac voice', 'prov.system.note': 'Built in. A Siri voice if you picked one.',
      'whisper.advice': 'Your Mac has {mem} GB of memory and {chip}, so {model} fits well.', 'whisper.cli': 'Whisper needs whisper.cpp on this Mac.',
      'whisper.free': '{free} free on this disk.', 'whisper.verify': 'Checking the download…', 'whisper.ready': 'Ready on this Mac',
      'whisper.bad': 'The download didn’t match its checksum, so it was removed. Try again.', 'whisper.space': 'Not enough space: {need} needed, {free} free.',
      'kokoro.ready': 'Kokoro is ready on this Mac.', 'kokoro.missing': 'Kokoro isn’t on this Mac yet (about 350 MB).',
      'ai.title': 'Which AI should Kira use?', 'ai.sub': 'Kira thinks with it. Change it anytime in Settings.',
      'ai.plans': 'With a subscription', 'ai.keys': 'With an API key', 'ai.local': 'On this Mac',
      'ai.claude': 'Claude Code', 'ai.claude.note': 'Your Claude plan (Pro or Max).', 'ai.codex': 'Codex CLI', 'ai.codex.note': 'Your ChatGPT plan, through OpenAI’s CLI.',
      'ai.cursor': 'Cursor Agent', 'ai.cursor.note': 'Your Cursor plan, through Cursor’s CLI.',
      'ai.anthropic': 'Anthropic API', 'ai.anthropic.note': 'Billed per use by Anthropic.', 'ai.openrouter': 'OpenRouter', 'ai.openrouter.note': 'Many models, billed per use by OpenRouter.',
      'ai.server': 'Custom server', 'ai.server.note': 'Any Claude-compatible API, like DeepSeek or vLLM.',
      'ai.ollama': 'Ollama', 'ai.lmstudio': 'LM Studio', 'ai.local.note': 'Free and private, on this Mac. Needs a strong model.', 'ai.local.none': 'Start Ollama or LM Studio, and Kira finds it here.',
      'ai.ok': 'Ready', 'ai.install': 'Not installed', 'ai.login': 'Not signed in', 'ai.upgrade': 'Needs a paid plan',
      'ai.privacy': 'What you ask, and your screen when you say “this”, go to the AI you pick.',
      'conn.title': 'What can Kira use for you?', 'conn.sub': 'Apps you connected in Claude. Choose how much Kira may do in each.',
      'conn.ask': 'Ask first', 'conn.allow': 'Always allow', 'conn.never': 'Never',
      'conn.readonly': 'Looking things up never asks. Sending, changing or deleting asks first, unless you pick Always allow.',
      'conn.none': 'No connected apps yet', 'conn.noneSub': 'Connect Gmail, Calendar or Drive on claude.ai, then set them here or in Settings.',
      'conn.open': 'Open claude.ai', 'conn.loading': 'Finding your connected apps…',
      'perm.title': 'Let Kira work on your Mac', 'perm.sub': 'macOS asks you for each one. Kira can’t switch them on by itself.',
      'perm.mic': 'Microphone', 'perm.mic.why': 'To hear you while you hold the shortcut.', 'perm.speech': 'Speech Recognition', 'perm.speech.why': 'To turn your words into text, on this Mac.',
      'perm.ax': 'Keyboard and mouse control', 'perm.ax.why': 'To click, type and move windows for you (Accessibility).',
      'perm.screen': 'Screen Recording', 'perm.screen.why': 'To see your screen when you say “this”.',
      'perm.auto': 'App control', 'perm.auto.why': 'To script apps like Finder and Mail (Automation).', 'perm.calendar': 'Calendar', 'perm.calendar.why': 'To read and add events when you ask.',
      'perm.chrome': 'Chrome pages', 'perm.chrome.why': 'To read and click web pages in Chrome.',
      'perm.allow': 'Allow', 'perm.on': 'On', 'perm.off': 'Off',
      'perm.all': 'Allow everything', 'perm.allSub': 'Opens each macOS switch in turn for you to flip, and gives Kira full access: it acts without asking first.',
      'perm.hold': 'Hold to confirm', 'perm.holding': 'Keep holding…', 'perm.fullOn': 'Full access is on. Undo it in Settings → Account & Access.',
      'perm.allNote': 'Kira still never runs rm, sudo or other commands that can’t be undone, and connectors set to Never stay blocked.',
      'perm.later': 'Anything you skip stays off. Kira asks when a task needs it.',
      'key.title': 'Try it now', 'key.hold': 'Hold {keys} and say hi', 'key.listening': 'Listening…', 'key.heard': 'Got it. That’s all it takes.',
      'key.dictate': 'To dictate into any text field, hold {fn}.', 'key.level': 'Microphone level', 'key.micOff': 'Allow the microphone first, one step back.',
      'done.title': 'You’re all set', 'done.sub': 'Kira lives in your menu bar. Hold {keys} anytime.', 'done.settings': 'Open Settings', 'done.tour': 'Take the tour', 'done.finish': 'Finish',
      'done.you': 'You', 'done.language': 'Language', 'done.hearing': 'Hearing', 'done.speaking': 'Speaking', 'done.ai': 'AI', 'done.access': 'Access',
      'done.ask': 'Asks first', 'done.full': 'Full access',
    },
    uz: {
      'chrome.skipIntro': 'Kirishni o‘tkazish', 'boot.cta': 'Kira’ni sozlash', 'chrome.mute': 'Ovozni o‘chirish', 'chrome.unmute': 'Ovozni yoqish',
      'common.back': 'Orqaga', 'common.next': 'Davom etish', 'common.skip': 'Hozircha o‘tkazish', 'common.test': 'Sinash', 'common.testing': 'Sinalmoqda…',
      'common.works': 'Ishlayapti', 'common.saved': 'Keychain’da saqlandi', 'common.keyPh': 'API kalitini qo‘ying', 'common.getKey': 'Kalit olish',
      'common.model': 'Model', 'common.voice': 'Ovoz', 'common.sample': 'Namunani eshitish', 'common.recommended': 'Tavsiya etiladi', 'common.free': 'Bepul',
      'common.install': 'O‘rnatish', 'common.signIn': 'Kirish', 'common.use': 'Tanlash', 'common.inUse': 'Tanlangan', 'common.remove': 'Kalitni o‘chirish',
      'common.download': 'Yuklab olish', 'common.pause': 'To‘xtatish', 'common.resume': 'Davom ettirish', 'common.delete': 'O‘chirish', 'common.checking': 'Tekshirilmoqda…',
      'common.address': 'Manzil', 'common.steps': 'Sozlash bosqichlari', 'common.step': '{total} dan {n}-bosqich',
      'name.first': 'Ism', 'name.last': 'Familiya (ixtiyoriy)', 'name.go': 'Davom etish', 'name.skip': 'O‘tkazish',
      'name.say': 'Boshqacha aytish', 'name.sayPh': 'Qanday aytiladi, masalan “Ha-san”',
      'greet.named': 'Salom, {name}! Tanishganimdan xursandman!', 'greet.none': 'Salom! Tanishganimdan xursandman!',
      'lang.title': 'Qaysi tilda gaplashasiz?', 'lang.sub': 'Kira shu tilda eshitadi, gapiradi va javob beradi. Almashtirib tursangiz, bir nechtasini tanlang.',
      'lang.search': 'Tillarni qidirish', 'lang.primary': 'Asosiy', 'lang.makePrimary': 'Asosiy qilish', 'lang.none': '“{q}” bo‘yicha til topilmadi.',
      'lang.ui': 'Kira menyulari tili', 'lang.hears': 'Apple eshitadi', 'lang.speaks': 'Kira gapiradi',
      'lang.hearApple': 'Apple {lang} tilida shu Mac’da eshitadi.', 'lang.hearNo': 'Apple {lang} tilini shu Mac’da eshita olmaydi. Keyingi qadamda Whisper yoki bulutli ovozni tanlang.',
      'lang.hearLoad': 'Apple’ning {lang} nutq modeli davom etganingizda yuklanadi.',
      'lang.speakKokoro': 'Kira {lang} tilida o‘z ovozi bilan, shu Mac’da gapiradi.', 'lang.speakMac': 'Kira {lang} tilida Mac ovozi bilan gapiradi.',
      'lang.speakNo': 'Bu Mac’dagi hech bir ovoz hali {lang} tilida gapirmaydi: Kira matn bilan javob beradi yoki keyingi qadamda bulutli ovoz tanlang.',
      'acct.title': 'Sozlamalarni saqlang', 'acct.sub': 'Hisob Kira sozlamalarini barcha Mac’laringizda saqlaydi.', 'acct.email': 'Email',
      'acct.continue': 'Email bilan davom etish', 'acct.google': 'Google bilan davom etish', 'acct.skip': 'Hisobsiz davom etish',
      'acct.soon': 'Hisoblar hali mavjud emas. Hisobsiz ham hammasi ishlaydi.',
      'voice.title': 'Kira qanday eshitsin va gapirsin?', 'voice.hear': 'Eshitish', 'voice.speak': 'Gapirish',
      'voice.data': 'Apple, Whisper va Kokoro hammasini shu Mac’da saqlaydi. Bulutli provayder ovozingizni (eshitish) yoki Kira javoblarini (gapirish) faqat Kira’dan foydalanayotganingizda oladi. Kalitlar Mac’ingizdagi Keychain’da turadi, hech qachon fayl yoki loglarda emas.',
      'voice.fallback': 'Provayder ishlamasa, Kira Apple va Kokoro’ga qaytadi.',
      'prov.apple': 'Apple, shu Mac’da', 'prov.apple.note': 'Bepul, kalitsiz. Ovozingiz bu Mac’dan chiqmaydi.',
      'prov.deepgram': 'Deepgram', 'prov.deepgram.hear': 'Nova: tez va aniq, ko‘p tillarda.', 'prov.deepgram.speak': 'Aura: tabiiy ovozlar, tez boshlanadi.',
      'prov.openai': 'OpenAI', 'prov.openai.hear': 'Matnga o‘girish, daqiqasiga to‘lov.', 'prov.openai.speak': 'Tabiiy ovozlar, belgi soniga to‘lov.',
      'prov.elevenlabs': 'ElevenLabs', 'prov.elevenlabs.speak': 'Ko‘p tillarda ifodali ovozlar.',
      'prov.custom': 'Maxsus server', 'prov.custom.note': 'OpenAI bilan mos har qanday nutq API’si.',
      'prov.whisper': 'Whisper, shu Mac’da', 'prov.whisper.note': 'Bepul va maxfiy. Modelni bir marta yuklab oladi.',
      'prov.kokoro': 'Kokoro, shu Mac’da', 'prov.kokoro.note': 'Bepul va maxfiy. Kira’ning o‘z ovozi.',
      'prov.system': 'Mac ovozi', 'prov.system.note': 'O‘rnatilgan. Tanlagan bo‘lsangiz, Siri ovozi.',
      'whisper.advice': 'Mac’ingizda {mem} GB xotira va {chip} bor, shuning uchun {model} mos keladi.', 'whisper.cli': 'Whisper uchun bu Mac’da whisper.cpp kerak.',
      'whisper.free': 'Diskda {free} bo‘sh joy bor.', 'whisper.verify': 'Yuklangan fayl tekshirilmoqda…', 'whisper.ready': 'Bu Mac’da tayyor',
      'whisper.bad': 'Yuklangan fayl nazorat summasiga mos kelmadi va o‘chirildi. Qaytadan urinib ko‘ring.', 'whisper.space': 'Joy yetmaydi: {need} kerak, {free} bo‘sh.',
      'kokoro.ready': 'Kokoro bu Mac’da tayyor.', 'kokoro.missing': 'Kokoro hali bu Mac’da yo‘q (taxminan 350 MB).',
      'ai.title': 'Kira qaysi AI’dan foydalansin?', 'ai.sub': 'Kira u bilan fikrlaydi. Istalgan payt Sozlamalarda o‘zgartirasiz.',
      'ai.plans': 'Obuna bilan', 'ai.keys': 'API kaliti bilan', 'ai.local': 'Shu Mac’da',
      'ai.claude': 'Claude Code', 'ai.claude.note': 'Claude obunangiz (Pro yoki Max).', 'ai.codex': 'Codex CLI', 'ai.codex.note': 'ChatGPT obunangiz, OpenAI CLI orqali.',
      'ai.cursor': 'Cursor Agent', 'ai.cursor.note': 'Cursor obunangiz, Cursor CLI orqali.',
      'ai.anthropic': 'Anthropic API', 'ai.anthropic.note': 'Anthropic foydalanishga qarab hisoblaydi.', 'ai.openrouter': 'OpenRouter', 'ai.openrouter.note': 'Ko‘p modellar, OpenRouter foydalanishga qarab hisoblaydi.',
      'ai.server': 'Maxsus server', 'ai.server.note': 'Claude bilan mos har qanday API, masalan DeepSeek yoki vLLM.',
      'ai.ollama': 'Ollama', 'ai.lmstudio': 'LM Studio', 'ai.local.note': 'Bepul va maxfiy, shu Mac’da. Kuchli model kerak.', 'ai.local.none': 'Ollama yoki LM Studio’ni ishga tushiring, Kira uni shu yerda topadi.',
      'ai.ok': 'Tayyor', 'ai.install': 'O‘rnatilmagan', 'ai.login': 'Kirilmagan', 'ai.upgrade': 'Pullik obuna kerak',
      'ai.privacy': 'So‘rovlaringiz va “bu” deganingizda ekraningiz siz tanlagan AI’ga boradi.',
      'conn.title': 'Kira siz uchun nimalardan foydalansin?', 'conn.sub': 'Claude’da ulagan ilovalaringiz. Har birida Kira qanchalik ish qilishini tanlang.',
      'conn.ask': 'Avval so‘rasin', 'conn.allow': 'Doim ruxsat', 'conn.never': 'Hech qachon',
      'conn.readonly': 'Ma’lumot qidirish hech qachon so‘ramaydi. Yuborish, o‘zgartirish yoki o‘chirishdan oldin so‘raydi, agar “Doim ruxsat” tanlamagan bo‘lsangiz.',
      'conn.none': 'Hali ulangan ilova yo‘q', 'conn.noneSub': 'claude.ai’da Gmail, Calendar yoki Drive’ni ulang, so‘ng shu yerda yoki Sozlamalarda belgilang.',
      'conn.open': 'claude.ai’ni ochish', 'conn.loading': 'Ulangan ilovalaringiz qidirilmoqda…',
      'perm.title': 'Kira Mac’ingizda ishlay olsin', 'perm.sub': 'macOS har biri uchun sizdan so‘raydi. Kira ularni o‘zi yoqa olmaydi.',
      'perm.mic': 'Mikrofon', 'perm.mic.why': 'Tugmani bosib turganingizda sizni eshitish uchun.', 'perm.speech': 'Nutqni aniqlash', 'perm.speech.why': 'Gaplaringizni shu Mac’da matnga aylantirish uchun.',
      'perm.ax': 'Klaviatura va sichqoncha boshqaruvi', 'perm.ax.why': 'Siz uchun bosish, yozish va oynalarni surish uchun (Accessibility).',
      'perm.screen': 'Ekranni yozib olish', 'perm.screen.why': '“Bu” deganingizda ekraningizni ko‘rish uchun.',
      'perm.auto': 'Ilovalarni boshqarish', 'perm.auto.why': 'Finder va Mail kabi ilovalarni boshqarish uchun (Automation).', 'perm.calendar': 'Taqvim', 'perm.calendar.why': 'So‘raganingizda tadbirlarni o‘qish va qo‘shish uchun.',
      'perm.chrome': 'Chrome sahifalari', 'perm.chrome.why': 'Chrome’dagi sahifalarni o‘qish va bosish uchun.',
      'perm.allow': 'Ruxsat berish', 'perm.on': 'Yoqilgan', 'perm.off': 'O‘chiq',
      'perm.all': 'Hammasiga ruxsat', 'perm.allSub': 'macOS kalitlarini birin-ketin ochadi, ularni siz yoqasiz; Kira’ga to‘liq ruxsat beradi: u oldindan so‘ramasdan ishlaydi.',
      'perm.hold': 'Tasdiqlash uchun bosib turing', 'perm.holding': 'Bosib turing…', 'perm.fullOn': 'To‘liq ruxsat yoqildi. Uni Sozlamalar → Hisob va ruxsatlar’da qaytarasiz.',
      'perm.allNote': 'Kira baribir rm, sudo kabi qaytarib bo‘lmaydigan buyruqlarni ishlatmaydi, “Hech qachon” belgilangan connectorlar ham yopiq qoladi.',
      'perm.later': 'O‘tkazib yuborganingiz o‘chiq qoladi. Vazifa uchun kerak bo‘lsa, Kira so‘raydi.',
      'key.title': 'Hozir sinab ko‘ring', 'key.hold': '{keys} ni bosib turing va salom deng', 'key.listening': 'Eshityapman…', 'key.heard': 'Tushundim. Bor-yo‘g‘i shu.',
      'key.dictate': 'Istalgan matn maydoniga aytib yozish uchun {fn} ni bosib turing.', 'key.level': 'Mikrofon darajasi', 'key.micOff': 'Avval mikrofonga ruxsat bering (bir qadam orqada).',
      'done.title': 'Hammasi tayyor', 'done.sub': 'Kira menyu qatorida yashaydi. Istalgan payt {keys} ni bosib turing.', 'done.settings': 'Sozlamalarni ochish', 'done.tour': 'Qisqa tanishuv', 'done.finish': 'Tugatish',
      'done.you': 'Siz', 'done.language': 'Til', 'done.hearing': 'Eshitish', 'done.speaking': 'Gapirish', 'done.ai': 'AI', 'done.access': 'Ruxsat',
      'done.ask': 'Avval so‘raydi', 'done.full': 'To‘liq ruxsat',
    },
    ru: {
      'chrome.skipIntro': 'Пропустить заставку', 'boot.cta': 'Настроить Kira', 'chrome.mute': 'Выключить звук', 'chrome.unmute': 'Включить звук',
      'common.back': 'Назад', 'common.next': 'Продолжить', 'common.skip': 'Пропустить', 'common.test': 'Проверить', 'common.testing': 'Проверяю…',
      'common.works': 'Работает', 'common.saved': 'Сохранено в Связке ключей', 'common.keyPh': 'Вставьте API-ключ', 'common.getKey': 'Получить ключ',
      'common.model': 'Модель', 'common.voice': 'Голос', 'common.sample': 'Прослушать', 'common.recommended': 'Рекомендуем', 'common.free': 'Бесплатно',
      'common.install': 'Установить', 'common.signIn': 'Войти', 'common.use': 'Выбрать', 'common.inUse': 'Выбрано', 'common.remove': 'Удалить ключ',
      'common.download': 'Скачать', 'common.pause': 'Пауза', 'common.resume': 'Продолжить', 'common.delete': 'Удалить', 'common.checking': 'Проверяю…',
      'common.address': 'Адрес', 'common.steps': 'Шаги настройки', 'common.step': 'Шаг {n} из {total}',
      'name.first': 'Имя', 'name.last': 'Фамилия (необязательно)', 'name.go': 'Продолжить', 'name.skip': 'Пропустить',
      'name.say': 'Произносится иначе', 'name.sayPh': 'Как произносить, например «Ха-сан»',
      'greet.named': 'Привет, {name}! Рада знакомству!', 'greet.none': 'Привет! Рада знакомству!',
      'lang.title': 'На каком языке вы говорите?', 'lang.sub': 'Kira будет слушать, говорить и отвечать на нём. Выберите несколько, если переключаетесь.',
      'lang.search': 'Поиск языка', 'lang.primary': 'Основной', 'lang.makePrimary': 'Сделать основным', 'lang.none': 'Нет языка по запросу «{q}».',
      'lang.ui': 'Язык меню Kira', 'lang.hears': 'Apple слышит', 'lang.speaks': 'Kira говорит',
      'lang.hearApple': 'Apple распознаёт {lang} на этом Mac.', 'lang.hearNo': 'Apple не распознаёт {lang} на этом Mac. Дальше выберите Whisper или облачный голос.',
      'lang.hearLoad': 'Модель речи Apple для языка «{lang}» скачается, когда вы продолжите.',
      'lang.speakKokoro': 'Kira говорит на языке «{lang}» своим голосом, на этом Mac.', 'lang.speakMac': 'Kira говорит на языке «{lang}» голосом Mac.',
      'lang.speakNo': 'На этом Mac пока нет голоса для языка «{lang}»: Kira ответит текстом, или выберите облачный голос дальше.',
      'acct.title': 'Сохраните настройки', 'acct.sub': 'Аккаунт хранит настройки Kira на всех ваших Mac.', 'acct.email': 'Email',
      'acct.continue': 'Продолжить с Email', 'acct.google': 'Продолжить с Google', 'acct.skip': 'Продолжить без аккаунта',
      'acct.soon': 'Аккаунтов пока нет. Всё работает и без него.',
      'voice.title': 'Как Kira будет слышать и говорить?', 'voice.hear': 'Слух', 'voice.speak': 'Речь',
      'voice.data': 'Apple, Whisper и Kokoro работают только на этом Mac. Облачный сервис получает ваш голос (слух) или ответы Kira (речь) только пока вы пользуетесь Kira. Ключи хранятся в Связке ключей, не в файлах и журналах.',
      'voice.fallback': 'Если сервис не отвечает, Kira возвращается к Apple и Kokoro.',
      'prov.apple': 'Apple, на этом Mac', 'prov.apple.note': 'Бесплатно, без ключа. Голос не покидает этот Mac.',
      'prov.deepgram': 'Deepgram', 'prov.deepgram.hear': 'Nova: быстро и точно, на многих языках.', 'prov.deepgram.speak': 'Aura: естественные голоса, быстрый старт.',
      'prov.openai': 'OpenAI', 'prov.openai.hear': 'Распознавание, оплата поминутно.', 'prov.openai.speak': 'Естественные голоса, оплата за символы.',
      'prov.elevenlabs': 'ElevenLabs', 'prov.elevenlabs.speak': 'Выразительные голоса на многих языках.',
      'prov.custom': 'Свой сервер', 'prov.custom.note': 'Любой речевой API, совместимый с OpenAI.',
      'prov.whisper': 'Whisper, на этом Mac', 'prov.whisper.note': 'Бесплатно и приватно. Модель скачивается один раз.',
      'prov.kokoro': 'Kokoro, на этом Mac', 'prov.kokoro.note': 'Бесплатно и приватно. Собственный голос Kira.',
      'prov.system': 'Голос Mac', 'prov.system.note': 'Встроенный. Голос Siri, если вы его выбрали.',
      'whisper.advice': 'У вашего Mac {mem} ГБ памяти и {chip}, поэтому подойдёт {model}.', 'whisper.cli': 'Для Whisper нужен whisper.cpp на этом Mac.',
      'whisper.free': 'Свободно на диске: {free}.', 'whisper.verify': 'Проверяю загрузку…', 'whisper.ready': 'Готово на этом Mac',
      'whisper.bad': 'Загрузка не совпала с контрольной суммой и удалена. Попробуйте ещё раз.', 'whisper.space': 'Мало места: нужно {need}, свободно {free}.',
      'kokoro.ready': 'Kokoro готов на этом Mac.', 'kokoro.missing': 'Kokoro ещё не установлен (около 350 МБ).',
      'ai.title': 'Какой ИИ будет у Kira?', 'ai.sub': 'Kira думает с его помощью. Меняется в любой момент в Настройках.',
      'ai.plans': 'По подписке', 'ai.keys': 'По API-ключу', 'ai.local': 'На этом Mac',
      'ai.claude': 'Claude Code', 'ai.claude.note': 'Ваша подписка Claude (Pro или Max).', 'ai.codex': 'Codex CLI', 'ai.codex.note': 'Ваша подписка ChatGPT, через CLI от OpenAI.',
      'ai.cursor': 'Cursor Agent', 'ai.cursor.note': 'Ваша подписка Cursor, через CLI от Cursor.',
      'ai.anthropic': 'Anthropic API', 'ai.anthropic.note': 'Оплата по использованию у Anthropic.', 'ai.openrouter': 'OpenRouter', 'ai.openrouter.note': 'Много моделей, оплата по использованию у OpenRouter.',
      'ai.server': 'Свой сервер', 'ai.server.note': 'Любой API, совместимый с Claude, например DeepSeek или vLLM.',
      'ai.ollama': 'Ollama', 'ai.lmstudio': 'LM Studio', 'ai.local.note': 'Бесплатно и приватно, на этом Mac. Нужна сильная модель.', 'ai.local.none': 'Запустите Ollama или LM Studio, и Kira найдёт их здесь.',
      'ai.ok': 'Готово', 'ai.install': 'Не установлен', 'ai.login': 'Вход не выполнен', 'ai.upgrade': 'Нужна платная подписка',
      'ai.privacy': 'Ваши запросы и экран, когда вы говорите «это», уходят выбранному ИИ.',
      'conn.title': 'Чем Kira может пользоваться?', 'conn.sub': 'Приложения, подключённые в Claude. Выберите, что Kira можно делать в каждом.',
      'conn.ask': 'Спрашивать', 'conn.allow': 'Всегда можно', 'conn.never': 'Никогда',
      'conn.readonly': 'Поиск никогда не спрашивает. Отправка, изменение и удаление спрашивают, если не выбрано «Всегда можно».',
      'conn.none': 'Подключённых приложений пока нет', 'conn.noneSub': 'Подключите Gmail, Календарь или Диск на claude.ai, потом настройте их здесь или в Настройках.',
      'conn.open': 'Открыть claude.ai', 'conn.loading': 'Ищу подключённые приложения…',
      'perm.title': 'Разрешите Kira работать на Mac', 'perm.sub': 'macOS спрашивает про каждое разрешение. Kira не может включить их сама.',
      'perm.mic': 'Микрофон', 'perm.mic.why': 'Чтобы слышать вас, пока вы держите сочетание.', 'perm.speech': 'Распознавание речи', 'perm.speech.why': 'Чтобы превращать речь в текст на этом Mac.',
      'perm.ax': 'Управление клавиатурой и мышью', 'perm.ax.why': 'Чтобы нажимать, печатать и двигать окна за вас (Универсальный доступ).',
      'perm.screen': 'Запись экрана', 'perm.screen.why': 'Чтобы видеть экран, когда вы говорите «это».',
      'perm.auto': 'Управление приложениями', 'perm.auto.why': 'Чтобы управлять Finder, Почтой и другими (Автоматизация).', 'perm.calendar': 'Календарь', 'perm.calendar.why': 'Чтобы читать и добавлять события по просьбе.',
      'perm.chrome': 'Страницы Chrome', 'perm.chrome.why': 'Чтобы читать страницы в Chrome и нажимать на них.',
      'perm.allow': 'Разрешить', 'perm.on': 'Вкл.', 'perm.off': 'Выкл.',
      'perm.all': 'Разрешить всё', 'perm.allSub': 'По очереди открывает переключатели macOS, а вы их включаете, и даёт Kira полный доступ: она действует, не спрашивая.',
      'perm.hold': 'Удерживайте для подтверждения', 'perm.holding': 'Удерживайте…', 'perm.fullOn': 'Полный доступ включён. Отменить: Настройки → Аккаунт и доступ.',
      'perm.allNote': 'Kira по-прежнему никогда не запускает rm, sudo и другие необратимые команды, а коннекторы с «Никогда» остаются закрыты.',
      'perm.later': 'Пропущенное останется выключенным. Kira спросит, когда понадобится.',
      'key.title': 'Попробуйте', 'key.hold': 'Удерживайте {keys} и скажите «привет»', 'key.listening': 'Слушаю…', 'key.heard': 'Поняла. Вот и всё.',
      'key.dictate': 'Чтобы диктовать в любое поле, удерживайте {fn}.', 'key.level': 'Уровень микрофона', 'key.micOff': 'Сначала разрешите микрофон, шагом раньше.',
      'done.title': 'Всё готово', 'done.sub': 'Kira живёт в строке меню. Удерживайте {keys} в любой момент.', 'done.settings': 'Открыть Настройки', 'done.tour': 'Короткий тур', 'done.finish': 'Готово',
      'done.you': 'Вы', 'done.language': 'Язык', 'done.hearing': 'Слух', 'done.speaking': 'Речь', 'done.ai': 'ИИ', 'done.access': 'Доступ',
      'done.ask': 'Спрашивает', 'done.full': 'Полный доступ',
    },
  };
  let ui = 'en';
  const t = (key, vars = {}) => String((STRINGS[ui] && STRINGS[ui][key]) ?? STRINGS.en[key] ?? key).replace(/\{(\w+)\}/g, (m, k) => vars[k] ?? m);
  const setUI = code => { ui = UI.includes(code) ? code : 'en'; return ui; };
  const uiFor = tag => { const base = String(tag || '').toLowerCase().split(/[-_]/)[0]; return UI.includes(base) ? base : 'en'; };
  // Fills [data-i18n] text, [data-i18n-ph] placeholders and [data-i18n-label] aria-labels under root.
  const apply = (root = document) => {
    root.querySelectorAll('[data-i18n]').forEach(e => { e.textContent = t(e.dataset.i18n); });
    root.querySelectorAll('[data-i18n-ph]').forEach(e => { e.placeholder = t(e.dataset.i18nPh); });
    root.querySelectorAll('[data-i18n-label]').forEach(e => { e.setAttribute('aria-label', t(e.dataset.i18nLabel)); });
    if (root === document) document.documentElement.lang = ui;
  };

  // ---- Languages Kira can be set to (BCP 47 with a region, as speech models want). Names come from the system, in the language itself and in English.
  const LANGS = ['af-ZA', 'ar-SA', 'az-AZ', 'be-BY', 'bg-BG', 'bn-IN', 'bs-BA', 'ca-ES', 'cs-CZ', 'cy-GB', 'da-DK', 'de-DE', 'de-AT', 'de-CH', 'el-GR',
    'en-US', 'en-GB', 'en-AU', 'en-CA', 'en-IN', 'en-IE', 'en-NZ', 'en-SG', 'en-ZA', 'es-ES', 'es-MX', 'es-US', 'es-AR', 'es-CO', 'et-EE', 'eu-ES', 'fa-IR',
    'fi-FI', 'fil-PH', 'fr-FR', 'fr-CA', 'fr-BE', 'fr-CH', 'ga-IE', 'gl-ES', 'gu-IN', 'he-IL', 'hi-IN', 'hr-HR', 'hu-HU', 'hy-AM', 'id-ID', 'is-IS',
    'it-IT', 'ja-JP', 'ka-GE', 'kk-KZ', 'km-KH', 'kn-IN', 'ko-KR', 'ky-KG', 'lo-LA', 'lt-LT', 'lv-LV', 'mk-MK', 'ml-IN', 'mn-MN', 'mr-IN', 'ms-MY',
    'my-MM', 'nb-NO', 'ne-NP', 'nl-NL', 'nl-BE', 'pa-IN', 'pl-PL', 'ps-AF', 'pt-BR', 'pt-PT', 'ro-RO', 'ru-RU', 'si-LK', 'sk-SK', 'sl-SI', 'sq-AL',
    'sr-RS', 'sv-SE', 'sw-KE', 'ta-IN', 'te-IN', 'tg-TJ', 'th-TH', 'tk-TM', 'tr-TR', 'uk-UA', 'ur-PK', 'uz-UZ', 'vi-VN', 'yue-HK', 'zh-CN', 'zh-TW', 'zu-ZA'];
  const cap = (s, tag) => s ? s.charAt(0).toLocaleUpperCase(tag) + s.slice(1) : s;
  const names = {};
  const langName = tag => {
    if (names[tag]) return names[tag];
    let native = tag, english = tag;
    try { native = cap(new Intl.DisplayNames([tag], { type: 'language' }).of(tag), tag); } catch (e) {}
    try { english = new Intl.DisplayNames(['en'], { type: 'language' }).of(tag); } catch (e) {}
    return (names[tag] = { native, english });
  };
  // Name in the interface language, for notes like "Apple listens in Uzbek".
  const langLabel = tag => { try { return new Intl.DisplayNames([ui], { type: 'language' }).of(tag.split('-')[0]); } catch (e) { return tag; } };
  const searchLangs = q => {
    const s = String(q || '').trim().toLocaleLowerCase();
    if (!s) return LANGS.slice();
    return LANGS.filter(tag => { const n = langName(tag); return [n.native, n.english, tag].some(x => x.toLocaleLowerCase().includes(s)); });
  };
  // The closest supported tag to what the Mac prefers ("uz-Latn-UZ" -> "uz-UZ", "en" -> "en-US").
  const nearest = tag => {
    const t2 = String(tag || '').replace('_', '-'), parts = t2.split('-'), base = parts[0].toLowerCase(), region = parts.slice(1).find(p => /^[A-Z]{2}$/i.test(p));
    return LANGS.find(l => l === `${base}-${(region || '').toUpperCase()}`) || LANGS.find(l => l.split('-')[0] === base) || null;
  };
  // Apple's speech models want a locale it lists; "en-US" matches "en_US" too.
  const sttHas = (tag, supported) => (supported || []).some(s => s.replace('_', '-').toLowerCase() === tag.toLowerCase());

  // ---- Speaking: Kokoro's own voices (kokoro-onnx language codes); other languages use a Mac voice when one is installed.
  const KOKORO = { 'en-US': ['af_heart', 'en-us'], 'en-CA': ['af_heart', 'en-us'], 'en-IN': ['af_heart', 'en-us'], 'en-SG': ['af_heart', 'en-us'],
    'en-GB': ['bf_emma', 'en-gb'], 'en-AU': ['bf_emma', 'en-gb'], 'en-IE': ['bf_emma', 'en-gb'], 'en-NZ': ['bf_emma', 'en-gb'], 'en-ZA': ['bf_emma', 'en-gb'],
    es: ['ef_dora', 'es'], fr: ['ff_siwis', 'fr-fr'], it: ['if_sara', 'it'], 'pt-BR': ['pf_dora', 'pt-br'], hi: ['hf_alpha', 'hi'] };
  const kokoroFor = tag => KOKORO[tag] || KOKORO[tag.split('-')[0]] || null;
  // How Kira will speak this language: Kokoro when it can, else a Mac voice when one is installed for it, else nothing.
  const voiceFor = (tag, env = {}) => kokoroFor(tag) && env.kokoro ? { engine: 'kokoro', voice: kokoroFor(tag)[0], lang: kokoroFor(tag)[1] }
    : (env.voices || []).some(v => v.replace('_', '-').toLowerCase().startsWith(tag.split('-')[0].toLowerCase())) ? { engine: 'system' } : null;

  // ---- Hearing and speaking providers. `key`: the Keychain account its key lives under (shared when one key serves both).
  const DEEPGRAM_OFFER = { text: 'New to Deepgram? You may get free starter credit.', url: 'https://console.deepgram.com/signup' };   // check the current offer before changing the words
  const STT = [
    { id: 'apple', name: 'prov.apple', note: 'prov.apple.note', badge: 'common.recommended', local: true },
    { id: 'whisper', name: 'prov.whisper', note: 'prov.whisper.note', local: true },
    { id: 'deepgram', name: 'prov.deepgram', note: 'prov.deepgram.hear', key: 'deepgram', keyUrl: 'https://console.deepgram.com/', models: ['nova-3', 'nova-2'], offer: DEEPGRAM_OFFER },
    { id: 'openai', name: 'prov.openai', note: 'prov.openai.hear', key: 'openai', keyUrl: 'https://platform.openai.com/api-keys', models: ['gpt-4o-mini-transcribe', 'gpt-4o-transcribe', 'whisper-1'] },
    { id: 'custom', name: 'prov.custom', note: 'prov.custom.note', key: 'custom-speech', base: true, models: [] },
  ];
  const TTS = [
    { id: 'kokoro', name: 'prov.kokoro', note: 'prov.kokoro.note', badge: 'common.recommended', local: true },
    { id: 'system', name: 'prov.system', note: 'prov.system.note', local: true },
    { id: 'deepgram', name: 'prov.deepgram', note: 'prov.deepgram.speak', key: 'deepgram', keyUrl: 'https://console.deepgram.com/', models: ['aura-2-thalia-en', 'aura-2-andromeda-en', 'aura-2-helena-en', 'aura-2-apollo-en', 'aura-2-arcas-en'], offer: DEEPGRAM_OFFER },
    { id: 'openai', name: 'prov.openai', note: 'prov.openai.speak', key: 'openai', keyUrl: 'https://platform.openai.com/api-keys', models: ['gpt-4o-mini-tts', 'tts-1', 'tts-1-hd'], voices: ['coral', 'nova', 'sage', 'shimmer', 'alloy', 'ash', 'verse'] },
    { id: 'elevenlabs', name: 'prov.elevenlabs', note: 'prov.elevenlabs.speak', key: 'elevenlabs', keyUrl: 'https://elevenlabs.io/app/settings/api-keys', models: ['eleven_flash_v2_5', 'eleven_multilingual_v2'], voiceId: true },
    { id: 'custom', name: 'prov.custom', note: 'prov.custom.note', key: 'custom-speech', base: true, models: [] },
  ];

  // ---- The AI. `client` and `apiBase` are what kira.py reads; `key` is the Keychain account of its API key.
  const AI = [
    { id: 'claude', group: 'plans', name: 'ai.claude', note: 'ai.claude.note', client: 'claude' },
    { id: 'codex', group: 'plans', name: 'ai.codex', note: 'ai.codex.note', client: 'codex' },
    { id: 'cursor', group: 'plans', name: 'ai.cursor', note: 'ai.cursor.note', client: 'cursor' },
    { id: 'anthropic', group: 'keys', name: 'ai.anthropic', note: 'ai.anthropic.note', client: 'claude', base: 'https://api.anthropic.com', key: 'anthropic', keyUrl: 'https://console.anthropic.com/settings/keys' },
    { id: 'openrouter', group: 'keys', name: 'ai.openrouter', note: 'ai.openrouter.note', client: 'claude', base: 'https://openrouter.ai/api', key: 'openrouter', keyUrl: 'https://openrouter.ai/settings/keys' },
    { id: 'server', group: 'keys', name: 'ai.server', note: 'ai.server.note', client: 'claude', base: '', key: 'custom-ai' },
  ];
  // Which Keychain account holds the key for a server address (Settings and setup agree on this without a stored pairing).
  const aiKeyFor = base => /api\.anthropic\.com/i.test(base || '') ? 'anthropic' : /openrouter\.ai/i.test(base || '') ? 'openrouter' : 'custom-ai';
  const aiFor = prefs => {
    const c = prefs.client || 'claude', base = String(prefs.apiBase || '').trim();
    if (c !== 'claude') return c;
    if (!base) return 'claude';
    return /api\.anthropic\.com/i.test(base) ? 'anthropic' : /openrouter\.ai/i.test(base) ? 'openrouter' : /localhost|127\.0\.0\.1/.test(base) ? 'local' : 'server';
  };

  // ---- Permissions, in the order setup asks. `id` is what Onboarding.grant / perms() use.
  const PERMS = [['mic', 'perm.mic'], ['speech', 'perm.speech'], ['ax', 'perm.ax'], ['screen', 'perm.screen'], ['auto', 'perm.auto'], ['calendar', 'perm.calendar'], ['chrome', 'perm.chrome']];
  // ---- What Kira may do in one connector. kira.py's gate enforces it (connector_policy).
  const POLICIES = [['ask', 'conn.ask'], ['allow', 'conn.allow'], ['never', 'conn.never']];
  const connectorName = n => String(n || '').replace(/^claude\.ai\s+/, '');

  // ---- Whisper (whisper.cpp ggml models) from the official ggerganov/whisper.cpp repository on Hugging Face; size in bytes, SHA-256 pinned.
  const WHISPER = [
    { id: 'tiny', file: 'ggml-tiny.bin', bytes: 77691713, sha256: 'be07e048e1e599ad46341c8d2a135645097a538221678b7acdd1b1919c6e1b21' },
    { id: 'base', file: 'ggml-base.bin', bytes: 147951465, sha256: '60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe' },
    { id: 'small', file: 'ggml-small.bin', bytes: 487601967, sha256: '1be3a9b2063867b937e64e2ec7483364a79917e157fa98c5d94b5c1fffea987b' },
    { id: 'medium', file: 'ggml-medium.bin', bytes: 1533763059, sha256: '6c14d5adee5f86394037b4e4e8b59f1673b6cee10e3cf0b11bbdbee79c156208' },
    { id: 'large-v3-turbo', file: 'ggml-large-v3-turbo.bin', bytes: 1624555275, sha256: '1fc70f774d38eb169993ac391eea357ef47c88757ef72ee5943879b7e8e2bc69' },
  ];
  // Which model this Mac runs well: memory first, then the chip (a starting table; tune it with measurements).
  // device: { mem: bytes, chip: "Apple M2 Pro", arm: bool }
  const recommendWhisper = device => {
    const gb = Math.round((device.mem || 0) / 2 ** 30), chip = String(device.chip || ''), big = /\b(Pro|Max|Ultra)\b/.test(chip);
    const id = !device.arm ? (gb >= 16 ? 'base' : 'tiny') : gb >= 32 && big ? 'large-v3-turbo' : gb >= 16 ? (big ? 'medium' : 'small') : 'base';
    return { id, gb, chip: chip.replace(/^Apple\s+/, '') || (device.arm ? 'Apple silicon' : 'an Intel chip') };
  };
  const bytes = n => n >= 1e9 ? (n / 1e9).toFixed(1).replace(/\.0$/, '') + ' GB' : Math.round(n / 1e6) + ' MB';

  // ---- The setup steps after the name, in order. ACCOUNT is off until Kira has a backend (see boot.html's ACCOUNT_STEP).
  const STEPS = ['language', 'account', 'voice', 'ai', 'connectors', 'permissions', 'hotkey', 'done'];

  return { UI, STRINGS, t, setUI, uiFor, apply, get ui() { return ui; }, LANGS, langName, langLabel, searchLangs, nearest, sttHas, KOKORO, kokoroFor, voiceFor,
           DEEPGRAM_OFFER, STT, TTS, AI, aiKeyFor, aiFor, PERMS, POLICIES, connectorName, WHISPER, recommendWhisper, bytes, STEPS };
})();
