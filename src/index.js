const m3uUrl = "https://raw.githubusercontent.com/zerodayip/Py/refs/heads/main/m3u8/playlist.m3u";
const usersUrl = "https://raw.githubusercontent.com/zerodayip/m3u-token-secure/refs/heads/main/users.json";
const webhookUrl = "https://canary.discord.com/api/webhooks/1364967293737766964/qz8YIsZEqo-E_StXVcgdrNQZjvFk5349nIdZ8z-LvP-Uzh69eqlUPBP9p-QGcrs12dZy";

async function handleRequest(request) {
    const url = new URL(request.url);
    let key = url.searchParams.get("key");
    let device_id = url.searchParams.get("device_id");  // Device ID'yi alıyoruz

    if (!key) {
        return new Response("Key bulunamadı!", { status: 400 });
    }

    if (!key.endsWith(".m3u")) {
        return new Response("Lütfen geçerli bir key ile .m3u uzantısını ekleyin.", { status: 400 });
    }

    key = key.slice(0, -4);

    let usersData;
    try {
        const usersResponse = await fetch(usersUrl);
        if (!usersResponse.ok) {
            throw new Error(`GitHub isteği başarısız oldu. Status: ${usersResponse.status}`);
        }
        usersData = await usersResponse.json();
    } catch (error) {
        return new Response("Kullanıcı verisi alınamadı: " + error.message, { status: 500 });
    }

    const user = Object.values(usersData).find(user => user.secret_key === key);

    if (!user) {
        return new Response("Geçersiz key!", { status: 403 });
    }

    const ip = request.headers.get("CF-Connecting-IP") || "Bilinmeyen IP";
    const userAgent = request.headers.get("User-Agent") || "Bilinmeyen User-Agent";
    const currentDate = new Date();
    const expireDate = new Date(user.expire_date);

    // Süresi dolmuş mu?
    if (currentDate > expireDate) {
        const expiredM3U = `#EXTM3U

#EXTINF:-1 tvg-name="SÜRE BİTTİ" tvg-logo="https://cdn-icons-png.flaticon.com/512/1062/1062832.png" group-title="IPTV SÜRENİZ DOLMUŞTUR!", IPTV SÜRENİZ DOLMUŞTUR!
https://iptv-info.local/sure-doldu1

#EXTINF:-1 tvg-name="SATIN AL" tvg-logo="https://cdn-icons-png.flaticon.com/512/1828/1828925.png" group-title="İLETİŞİME GEÇİNİNİZ.", IPTV SÜRESİ UZATMAK İÇİN BİZİMLE İLETİŞİME GEÇİN!
https://iptv-info.local/sure-doldu2`;

        const expiredM3UWithInfo = appendExpireInfo(expiredM3U, expireDate);

        await sendDiscordNotification("Token Süresi Dolmuş", key, device_id, ip, userAgent, 15158332);

        return new Response(expiredM3UWithInfo, {
            headers: { "Content-Type": "text/plain" }
        });
    }

    // Device ID kontrolü
    if (user.device_id && device_id && user.device_id !== device_id) {
        await sendDiscordNotification("Token Başka Cihazda Kullanıldı", key, device_id, ip, userAgent, 16776960);

        const warningM3U = `#EXTM3U

#EXTINF:-1 tvg-name="UYARI" tvg-logo="https://cdn-icons-png.flaticon.com/512/595/595067.png" group-title="BU TOKEN BAŞKA BİR CİHAZDA KULLANILMIŞ!", LÜTFEN DESTEK ALINIZ...
http://iptv-info.local/token-hatasi`;

        return new Response(warningM3U, {
            headers: { "Content-Type": "text/plain" }
        });
    }

    // İlk kullanımda device_id kaydet (eğer boşsa)
    if (!user.device_id && device_id) {
        user.device_id = device_id;
    }

    // Normal kullanım
    let m3uData = await fetchM3UData();
    m3uData = appendExpireInfo(m3uData, expireDate);

    user.used = true;
    user.device_id = device_id;

    await sendDiscordNotification("Yeni Token Kullanımı", key, device_id, ip, userAgent, 3066993);

    return new Response(m3uData, {
        headers: { "Content-Type": "text/plain" }
    });
}

async function fetchM3UData() {
    const response = await fetch(m3uUrl, {
        headers: {
            "Authorization": `Bearer ${GH_TOKEN}`,
        }
    });
    if (!response.ok) {
        throw new Error("GitHub'dan M3U verisi alınamadı");
    }
    return await response.text();
}

function appendExpireInfo(m3uData, expireDate) {
    const expireString = expireDate.toLocaleString("tr-TR", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
    });

    const expireInfo = `#EXTINF:-1 tvg-name="BİLGİ" tvg-logo="https://cdn-icons-png.flaticon.com/512/1828/1828970.png" group-title="SON TARİH: ${expireString}",...
http://iptv-info.local/expire`;

    m3uData = m3uData.replace(/^#EXTM3U\s*/m, `#EXTM3U\n${expireInfo}\n`);

    return m3uData;
}

async function sendDiscordNotification(title, key, device_id, ip, userAgent, color) {
    const discordMessage = {
        embeds: [
            {
                title: title,
                description: `Token: ${key}\nDevice ID: ${device_id || "Yok"}\nIP: ${ip}\nUser-Agent: ${userAgent}`,
                color: color,
                fields: [
                    {
                        name: "Token Bilgisi",
                        value: `Token: ${key}\nDevice ID: ${device_id || "Boş"}\nIP: ${ip}\nUser-Agent: ${userAgent}`
                    }
                ],
                footer: {
                    text: `IPTV Sistem Bilgisi | ${new Date().toLocaleString("tr-TR")}`
                },
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
