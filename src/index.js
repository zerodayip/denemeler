const m3uUrl = "https://raw.githubusercontent.com/zerodayip/Py/refs/heads/main/m3u8/playlist.m3u";
const usersUrl = "https://raw.githubusercontent.com/zerodayip/m3u-token-secure/refs/heads/main/users.json";
const webhookUrl = "https://canary.discord.com/api/webhooks/1364967293737766964/qz8YIsZEqo-E_StXVcgdrNQZjvFk5349nIdZ8z-LvP-Uzh69eqlUPBP9p-QGcrs12dZy";

// GH_TOKEN dışarıdan geliyor (Worker Secret)
const GH_TOKEN = SECRET_GH_TOKEN;

// KV Namespace bağlantısı (Cloudflare'da oluşturulan KV Namespace adı)
const TOKENS_KV = TOKENS_DB; // Worker binding olarak eklenmeli

async function handleRequest(request) {
    const url = new URL(request.url);
    const username = url.searchParams.get("user");
    const password = url.searchParams.get("pass");

    if (!username || !password) {
        return new Response("Kullanıcı adı ve şifre gerekli!", { status: 400 });
    }

    // Kullanıcıları çek (users.json)
    let usersData;
    try {
        const res = await fetch(usersUrl);
        if (!res.ok) throw new Error(`Kullanıcılar alınamadı, status: ${res.status}`);
        usersData = await res.json();
    } catch (e) {
        return new Response("Kullanıcı verisi alınamadı: " + e.message, { status: 500 });
    }

    const user = Object.values(usersData).find(u => u.username === username && u.password === password);
    if (!user) {
        return new Response("Geçersiz kullanıcı adı veya şifre!", { status: 403 });
    }

    const now = new Date();
    const expireDate = new Date(user.expire_date);
    if (now > expireDate) {
        await sendDiscordNotification("Token Süresi Dolmuş", username, null, 15158332);

        const expiredM3U = `#EXTM3U

#EXTINF:-1 tvg-name="SÜRE BİTTİ" tvg-logo="https://cdn-icons-png.flaticon.com/512/1062/1062832.png" group-title="IPTV SÜRENİZ DOLMUŞTUR!", IPTV SÜRENİZ DOLMUŞTUR!
https://iptv-info.local/sure-doldu1

#EXTINF:-1 tvg-name="SATIN AL" tvg-logo="https://cdn-icons-png.flaticon.com/512/1828/1828925.png" group-title="İLETİŞİME GEÇİNİNİZ.", IPTV SÜRESİ UZATMAK İÇİN BİZİMLE İLETİŞİME GEÇİN!
https://iptv-info.local/sure-doldu2`;

        return new Response(expiredM3U, {
            headers: { "Content-Type": "text/plain" }
        });
    }

    // KV'den kullanıcı aktif mi kontrol et
    const activeKey = `active_${username}`;
    const activeValue = await TOKENS_KV.get(activeKey);

    if (activeValue === "true") {
        // Başka bir cihazda aktif demek, hata ver
        await sendDiscordNotification("Token Başka Cihazda Kullanıldı", username, null, 16776960);

        const warningM3U = `#EXTM3U

#EXTINF:-1 tvg-name="UYARI" tvg-logo="https://cdn-icons-png.flaticon.com/512/595/595067.png" group-title="BU TOKEN BAŞKA BİR CİHAZDA KULLANILMIŞ!", LÜTFEN DESTEK ALINIZ...
http://iptv-info.local/token-hatasi`;

        return new Response(warningM3U, {
            headers: { "Content-Type": "text/plain" }
        });
    }

    // M3U'yu GH_TOKEN ile çek
    let m3uData;
    try {
        const res = await fetch(m3uUrl, {
            headers: {
                "Authorization": `Bearer ${GH_TOKEN}`,
            },
        });
        if (!res.ok) throw new Error("M3U dosyası alınamadı");
        m3uData = await res.text();
    } catch (err) {
        return new Response("M3U verisi alınamadı: " + err.message, { status: 500 });
    }

    // M3U içine expire info ekle
    m3uData = appendExpireInfo(m3uData, expireDate);

    // Kullanıcıyı aktif yap (KV’ye kaydet)
    await TOKENS_KV.put(activeKey, "true");

    await sendDiscordNotification("Yeni Token Kullanımı", username, null, 3066993);

    return new Response(m3uData, {
        headers: { "Content-Type": "text/plain" }
    });
}

function appendExpireInfo(m3uData, expireDate) {
    const expireString = expireDate.toLocaleString("tr-TR", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
    });

    const expireInfo = `#EXTINF:-1 tvg-name="BİLGİ" tvg-logo="https://cdn-icons-png.flaticon.com/512/1828/1828970.png" group-title="SON TARİH: ${expireString}", IPTV SÜRENİZİN BİTİŞ TARİHİ...
http://iptv-info.local/expire`;

    m3uData = m3uData.replace(/^#EXTM3U\s*/m, `#EXTM3U\n${expireInfo}\n`);

    return m3uData;
}

async function sendDiscordNotification(title, user, ip, color) {
    const discordMessage = {
        embeds: [
            {
                title: title,
                description: `Kullanıcı: ${user}` + (ip ? `\nIP: ${ip}` : ""),
                color: color,
                footer: { text: `IPTV Sistem Bilgisi | ${new Date().toLocaleString()}` },
            }
        ]
    };

    await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(discordMessage),
    });
}

addEventListener("fetch", event => {
    event.respondWith(handleRequest(event.request));
});
